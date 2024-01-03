import uuid

from src.main.python.plotlyst.core.domain import Topic, TopicType

ecological_topics = [
    Topic('Races', TopicType.Worldbuilding, uuid.UUID('882e3c1c-acf1-4590-a6d9-3875ab65fb89'), icon='ei.person'),
    Topic('Fauna', TopicType.Worldbuilding, uuid.UUID('0aa32bef-e901-49ca-b642-8c5b94a3022c'), icon='mdi.bird'),
    Topic('Fiona', TopicType.Worldbuilding, uuid.UUID('c97351b8-3b3c-4a16-8560-be9b1fcfecdc'), icon='fa5s.leaf'),
    Topic('Pets', TopicType.Worldbuilding, uuid.UUID('a725a343-9e84-4a63-a7d1-908895082086'), icon='fa5s.paw'),
]

cultural_topics = [
    Topic('Art', TopicType.Worldbuilding, uuid.UUID('b4122220-7c7c-44a4-b4dd-24a4ae02bd7e'), icon='mdi.palette'),
    Topic('Music', TopicType.Worldbuilding, uuid.UUID('b01e1938-9918-49ff-aa98-ec646c3c95b2'), icon='fa5s.music'),
    Topic('Fashion', TopicType.Worldbuilding, uuid.UUID('481c9d9f-9af3-475f-b837-ec786908832b'), icon='fa5s.tshirt'),
    Topic('Architecture', TopicType.Worldbuilding, uuid.UUID('94a13f82-4e5c-49fa-8df4-a9c89548a90d'),
          icon='ri.building-2-line'),
    Topic('Cuisine', TopicType.Worldbuilding, uuid.UUID('d65b389e-6052-4fd7-b820-2ee83e0f658c'),
          icon='mdi.food-turkey'),
    Topic('Etiquette', TopicType.Worldbuilding, uuid.UUID('024898e7-443e-4e64-940d-178303dd2d3a'),
          icon='fa5s.hands-helping'),
    Topic('Taboos', TopicType.Worldbuilding, uuid.UUID('851dec55-b383-43fd-86b6-9ea8af743b52'),
          icon='mdi.block-helper'),
    Topic('Sports', TopicType.Worldbuilding, uuid.UUID('2c3cd22b-27c8-4ec7-bd32-58edfd30174c'), icon='mdi.soccer'),
    Topic('Games', TopicType.Worldbuilding, uuid.UUID('7afc14ea-22e2-4837-8a41-83134c2ae1e9'), icon='fa5s.gamepad'),
    Topic('Morals', TopicType.Worldbuilding, uuid.UUID('c01a8b01-ec75-4e45-a5c8-05e69d05a11d'),
          icon='fa5s.balance-scale'),
    Topic('Rituals', TopicType.Worldbuilding, uuid.UUID('66c0088f-fa8a-4186-bb31-7fbd9d3bdcc9'), icon='fa5s.hands'),
    Topic('Festivals', TopicType.Worldbuilding, uuid.UUID('b08441a7-d949-4c2d-853a-7d52b52d992d'),
          icon='mdi.party-popper'),
    Topic('Entertainment', TopicType.Worldbuilding, uuid.UUID('09f96b9f-401f-4f8b-bf4d-f8c40118da72'),
          icon='mdi.popcorn')
]
historical_topics = [
    Topic('Legends', TopicType.Worldbuilding, uuid.UUID('6f8c672e-bc61-4a43-8737-090151fed2b5'), icon='mdi6.bow-arrow'),
    Topic('Fossils', TopicType.Worldbuilding, uuid.UUID('abe594a9-33e9-46bc-b229-bfb3305415fc'), icon='mdi.bone'),
    Topic('Artifacts', TopicType.Worldbuilding, uuid.UUID('a5700efd-bdac-4961-8cb3-c70bb0907383'),
          icon='mdi.treasure-chest'),
    Topic('Monuments', TopicType.Worldbuilding, uuid.UUID('95e702a5-4d34-49c5-9e03-a590207c0d5e'), icon='fa5s.monument')
]
linguistic_topics = [
    Topic('Alphabet', TopicType.Worldbuilding, uuid.UUID('91409386-4e1a-4e92-9a79-cad71e016bbe'),
          icon='mdi.alphabetical'),
    Topic('Slang', TopicType.Worldbuilding, uuid.UUID('5433fda2-de02-48cb-832b-67f4616ab4a3'),
          icon='mdi6.message-question-outline'),
    Topic('Curses', TopicType.Worldbuilding, uuid.UUID('20e90f8a-4e03-4e81-bcaa-63f05ea813fc'),
          icon='mdi6.message-flash-outline'),
    Topic('Communication', TopicType.Worldbuilding, uuid.UUID('c8a5da02-02b3-4174-b099-416b327db80a'),
          icon='fa5s.paper-plane')
]
technological_topics = [
    Topic('Medicine', TopicType.Worldbuilding, uuid.UUID('318da662-a846-4c21-a3f0-6d8f8f89a4a5'), icon='fa5s.syringe'),
    Topic('Tools', TopicType.Worldbuilding, uuid.UUID('3ad00ec4-2a1f-49ff-8c57-814253e3c96e'), icon='fa5s.tools'),
    Topic('Gadgets', TopicType.Worldbuilding, uuid.UUID('a8c0e4b7-fbca-4755-ac6b-8c9506e71e39'),
          icon='fa5s.mobile-alt'),
    Topic('Arms', TopicType.Worldbuilding, uuid.UUID('57824de0-07e1-465d-b9db-a3e2257d1aae'), icon='mdi.knife-military')
]
economic_topics = [
    Topic('Currency', TopicType.Worldbuilding, uuid.UUID('b62ecc86-d3ee-4600-bbcd-eb3fed4661a5'), icon='ph.coin-bold'),
    Topic('Businesses', TopicType.Worldbuilding, uuid.UUID('6e5267d9-abd0-4210-ad1d-671551939dd0'),
          icon='ei.shopping-cart'),
    Topic('Factories', TopicType.Worldbuilding, uuid.UUID('2837b2cb-299d-41f0-8690-4132e017d2b1'), icon='mdi.factory'),
    Topic('Resources', TopicType.Worldbuilding, uuid.UUID('be6bb804-75f9-45cb-b893-85df85280dd7'), icon='mdi.water'),
    Topic('Rare goods', TopicType.Worldbuilding, uuid.UUID('3583264c-870b-4d78-b63a-382023e30e70'), icon='fa5s.gem')
]
infrastructural_topics = [
    Topic('Water system', TopicType.Worldbuilding, uuid.UUID('7333bed6-bc0e-41f9-9a83-a87fd82d1c29'),
          icon='mdi.water-well'),
    Topic('Power system', TopicType.Worldbuilding, uuid.UUID('78d3c0a6-479b-481b-9d14-29f002ea4f07'),
          icon='fa5b.superpowers'),
    Topic('Waste system', TopicType.Worldbuilding, uuid.UUID('186dea63-0292-4e28-a113-51ad44e6d18b'), icon='mdi.pipe'),
    Topic('Deathcare', TopicType.Worldbuilding, uuid.UUID('2c93de12-ba6d-4bdb-bf8a-1494882468d2'),
          icon='mdi.grave-stone'),
    Topic('Transportation', TopicType.Worldbuilding, uuid.UUID('69bc684e-7fc6-4566-a114-af7206424fe9'),
          icon='fa5s.train'),
    Topic('Education', TopicType.Worldbuilding, uuid.UUID('6de9799d-5858-4811-b3e5-9ea9a5077e75'),
          icon='fa5s.graduation-cap'),
    Topic('Agriculture', TopicType.Worldbuilding, uuid.UUID('875683dd-6322-4011-8399-ddb278a58e09'), icon='mdi.corn'),
    Topic('Healthcare', TopicType.Worldbuilding, uuid.UUID('34c30a3d-4b35-4999-a2f5-f8d0e74f4f58'),
          icon='mdi.hospital-box')
]
religious_topics = []
fantastic_topics = []
nefarious_topics = []
environmental_topics = []

Topic('Gods', TopicType.Worldbuilding, uuid.UUID('e842e5de-2795-4780-bf5d-c3d06e2893c6'), icon='ri.thunderstorms-fill')
Topic('Religions', TopicType.Worldbuilding, uuid.UUID('9e276172-2e47-4ba5-b7a2-bf2da6cb4481'), icon='fa5s.church')
Topic('Afterlife', TopicType.Worldbuilding, uuid.UUID('b8bda0ad-f9f7-4e7b-873c-121b4157e4a4'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('a63ebf22-7323-489c-a3ac-9048c82905c8'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('6a1b6516-b1ba-4215-9fc9-f7d2d1acc71a'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('213fab5e-a522-4e6a-ac03-0ae851706404'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('8d25f651-dd2e-4d34-814e-09b5c91cd26b'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('562efc59-4fdf-4ebb-ab64-b25555658402'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('e6303c7c-0ba7-4ea8-9c45-b37d9dba8469'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('23604779-52e0-43c7-96b9-bbd08cde8ade'), icon='')
Topic('', TopicType.Worldbuilding, uuid.UUID('afa517d6-d964-4514-b4b1-7673f7b5c969'), icon='')
