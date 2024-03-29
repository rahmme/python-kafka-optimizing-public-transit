"""Defines trends calculations for stations"""
import logging

import faust

logger = logging.getLogger(__name__)


# Faust will ingest records from Kafka in this format
class Station(faust.Record):
    stop_id: int
    direction_id: str
    stop_name: str
    station_name: str
    station_descriptive_name: str
    station_id: int
    order: int
    red: bool
    blue: bool
    green: bool


# Faust will produce records to Kafka in this format
class TransformedStation(faust.Record):
    station_id: int
    station_name: str
    order: int
    line: str


def transform(station):
    line = ""
    if station.red:
        line = "red"
    elif station.blue:
        line = "blue"
    elif station.blue:
        line = "green"

    return TransformedStation(
        station.station_id,
        station.station_name,
        station.order,
        line
    )


app = faust.App("stations-stream", broker="kafka://localhost:9092", store="memory://")
topic = app.topic("org.chicago.cta.jdbc.source.stations", value_type=Station)
out_topic = app.topic("org.chicago.cta.transformed.stations", partitions=1)
table = app.Table(
    "org.chicago.cta.transformed.stations",
    default=TransformedStation,
    partitions=1,
    changelog_topic=out_topic,
)


@app.agent(topic)
async def stationevent(stationevents):
    stationevents.add_processor(transform)
    async for se in stationevents:
        table[se.station_id] = se


if __name__ == "__main__":
    app.main()
