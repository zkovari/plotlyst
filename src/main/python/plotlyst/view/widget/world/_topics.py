import uuid

from src.main.python.plotlyst.core.domain import Topic, TopicType

ecological_topics = [
    Topic('Races', TopicType.Worldbuilding, uuid.UUID('882e3c1c-acf1-4590-a6d9-3875ab65fb89'), icon='ei.person'),
    Topic('Fauna', TopicType.Worldbuilding, uuid.UUID('0aa32bef-e901-49ca-b642-8c5b94a3022c'), icon='mdi.bird'),
    Topic('Fiona', TopicType.Worldbuilding, uuid.UUID('c97351b8-3b3c-4a16-8560-be9b1fcfecdc'), icon='fa5s.leaf'),
    Topic('Pets', TopicType.Worldbuilding, uuid.UUID('a725a343-9e84-4a63-a7d1-908895082086'), icon='fa5s.paw'),
]
