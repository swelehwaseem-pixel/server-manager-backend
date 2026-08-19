import httpx

@router.get("/logs/query")
async def query_loki(query: str, start: int, end: int):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://loki:3100/loki/api/v1/query_range",
            params={"query": query, "start": start, "end": end}
        )
        return resp.json()
