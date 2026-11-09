import asyncio
from Flights import search_flights, find_best_dates

async def main():
    result = await search_flights(
        origin="HKG",
        destination,
        departure_date,
        return_date,
        travel_class="Premium Economy",
        nonstop_only=True,
        region)
    print(result)


asyncio.run(main())