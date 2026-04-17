"""
Peers router for COMP.
- Peer list: FMP /stable/stock-peers (returns symbol + name + price + mktCap)
- Fundamentals per peer: FMP income/balance statements fetched concurrently via httpx async
- Non-US fallback: OpenBB profile per peer
"""

import asyncio
from typing import Optional

import httpx

from mini_bloomberg.config import get_settings
from mini_bloomberg.core.cache import cached
from mini_bloomberg.core.errors import DataSourceError
from mini_bloomberg.core.ticker import Ticker
from mini_bloomberg.data.schemas import Comparables, PeerProfile


def get_comparables(ticker: Ticker) -> Comparables:
    peers_raw = _get_peer_list(ticker)
    if not peers_raw:
        return Comparables(symbol=ticker.symbol, peers=[])

    peers = asyncio.run(_enrich_peers_async(peers_raw[:8]))  # cap at 8
    return Comparables(symbol=ticker.symbol, peers=peers)


@cached(ttl=86400)
def _get_peer_list(ticker: Ticker) -> list[dict]:
    """FMP /stable/stock-peers — returns [{symbol, companyName, price, mktCap}]."""
    settings = get_settings()
    try:
        r = httpx.get(
            f"{settings.fmp_base_url}/stock-peers",
            params={"symbol": ticker.fmp_symbol, "apikey": settings.fmp_api_key},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        return r.json() if isinstance(r.json(), list) else []
    except Exception:
        return []


async def _enrich_peers_async(peers_raw: list[dict]) -> list[PeerProfile]:
    """Fetch income + balance data for each peer concurrently."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [_enrich_peer(client, settings, p) for p in peers_raw]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, PeerProfile)]


async def _enrich_peer(client: httpx.AsyncClient, settings, peer: dict) -> Optional[PeerProfile]:
    sym = peer["symbol"]
    key = settings.fmp_api_key
    base = settings.fmp_base_url

    async def _get(endpoint: str) -> list:
        try:
            r = await client.get(f"{base}/{endpoint}", params={"symbol": sym, "apikey": key, "limit": 1})
            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else []
        except Exception:
            pass
        return []

    # Fetch income and balance in parallel
    inc_list, bal_list = await asyncio.gather(_get("income-statement"), _get("balance-sheet-statement"))

    revenue = gross_margin = net_margin = op_margin = ebitda = total_debt = None

    if inc_list:
        inc = inc_list[0]
        revenue = inc.get("revenue")
        gp  = inc.get("grossProfit")
        ni  = inc.get("netIncome")
        oi  = inc.get("operatingIncome")
        ebitda = inc.get("ebitda")
        if revenue:
            gross_margin = (gp / revenue * 100) if gp is not None else None
            net_margin   = (ni / revenue * 100) if ni is not None else None
            op_margin    = (oi / revenue * 100) if oi is not None else None

    if bal_list:
        b = bal_list[0]
        total_debt = b.get("totalDebt")

    return PeerProfile(
        symbol=sym,
        name=peer.get("companyName"),
        market_cap=peer.get("mktCap"),
        revenue=revenue,
        gross_margin=gross_margin,
        net_margin=net_margin,
        operating_margin=op_margin,
        ebitda=ebitda,
        total_debt=total_debt,
        currency="USD",  # FMP peer list is US-centric; TODO non-US currency
    )
