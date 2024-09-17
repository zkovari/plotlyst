import uuid

from plotlyst.core.domain import Topic, TopicType

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
    Topic('History', TopicType.Worldbuilding, uuid.UUID('5420df8b-d988-429f-8ff1-689cd72d5bf7'), icon='mdi.bank'),
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
          icon='mdi6.horse-human'),
    Topic('Education', TopicType.Worldbuilding, uuid.UUID('6de9799d-5858-4811-b3e5-9ea9a5077e75'),
          icon='fa5s.graduation-cap'),
    Topic('Agriculture', TopicType.Worldbuilding, uuid.UUID('875683dd-6322-4011-8399-ddb278a58e09'), icon='mdi.corn'),
    Topic('Healthcare', TopicType.Worldbuilding, uuid.UUID('34c30a3d-4b35-4999-a2f5-f8d0e74f4f58'),
          icon='mdi.hospital-box')
]
religious_topics = [
    Topic('Gods', TopicType.Worldbuilding, uuid.UUID('e842e5de-2795-4780-bf5d-c3d06e2893c6'),
          icon='ri.thunderstorms-fill'),
    Topic('Religions', TopicType.Worldbuilding, uuid.UUID('9e276172-2e47-4ba5-b7a2-bf2da6cb4481'), icon='fa5s.church'),
    Topic('Sacred texts', TopicType.Worldbuilding, uuid.UUID('a63ebf22-7323-489c-a3ac-9048c82905c8'),
          icon='fa5s.scroll'),
    Topic('Prophecies', TopicType.Worldbuilding, uuid.UUID('6a1b6516-b1ba-4215-9fc9-f7d2d1acc71a'),
          icon='mdi6.crystal-ball')
]
fantastic_topics = [
    Topic('Magic', TopicType.Worldbuilding, uuid.UUID('562efc59-4fdf-4ebb-ab64-b25555658402'), icon='fa5s.magic'),
    Topic('Constructs', TopicType.Worldbuilding, uuid.UUID('e6303c7c-0ba7-4ea8-9c45-b37d9dba8469'), icon='mdi.robot'),
    Topic('Paranormal', TopicType.Worldbuilding, uuid.UUID('23604779-52e0-43c7-96b9-bbd08cde8ade'), icon='mdi6.ghost'),
    Topic('Aliens', TopicType.Worldbuilding, uuid.UUID('8d25f651-dd2e-4d34-814e-09b5c91cd26b'), icon='mdi.alien'),
    Topic('Magical creatures', TopicType.Worldbuilding, uuid.UUID('213fab5e-a522-4e6a-ac03-0ae851706404'),
          icon='fa5s.dragon'),
    Topic('Legendary items', TopicType.Worldbuilding, uuid.UUID('afa517d6-d964-4514-b4b1-7673f7b5c969'),
          icon='mdi6.axe-battle')
]
nefarious_topics = [
    Topic('Outlaws', TopicType.Worldbuilding, uuid.UUID('f6768a15-6b68-474b-a6db-982ffbb5b6f0'), icon='mdi.robber'),
    Topic('Crime', TopicType.Worldbuilding, uuid.UUID('add66039-19b6-4534-afcf-adf85a7f36ff'), icon='mdi.knife'),
    Topic('Cults', TopicType.Worldbuilding, uuid.UUID('5a114e40-6f9e-4c1c-9442-b337e9af5497'), icon='mdi.pentagram'),
    Topic('Corruption', TopicType.Worldbuilding, uuid.UUID('4519bef9-accd-4e27-865c-7e320fb6c2f3'), icon='mdi.sack'),
    Topic('Disease', TopicType.Worldbuilding, uuid.UUID('72f2c4b6-80a1-41ec-bc2a-984598868e21'), icon='mdi.virus'),
    Topic('Espionage', TopicType.Worldbuilding, uuid.UUID('79218b0d-1c30-4a41-9b4b-46ebe2b19e6b'), icon='ri.spy-fill'),
    Topic('Curses', TopicType.Worldbuilding, uuid.UUID('f4030cbf-28e6-4a57-95a5-b6d12d4d2ed9'), icon='fa5s.skull'),
    Topic('Forbidden tech', TopicType.Worldbuilding, uuid.UUID('da24909b-83b1-4f67-b841-0e0293c9d97c'),
          icon='fa5s.biohazard'),
]
environmental_topics = [
    Topic('Forests', TopicType.Worldbuilding, uuid.UUID('8c3526fc-daa5-47c9-888c-010f1bd475f8'), icon='mdi6.forest'),
    Topic('Mountains', TopicType.Worldbuilding, uuid.UUID('0a0a254c-c2fe-4235-94ec-41d9d3715bd0'),
          icon='fa5s.mountain'),
    Topic('Weather', TopicType.Worldbuilding, uuid.UUID('2fe12691-ce5b-42d6-b055-8e6472e09714'),
          icon='mdi.weather-lightning-rainy'),
    Topic('Natural hazards', TopicType.Worldbuilding, uuid.UUID('929b4a0a-4a59-4bc4-aa58-c9dc643b7eb5'),
          icon='mdi.weather-hurricane'),
    Topic('Islands', TopicType.Worldbuilding, uuid.UUID('95a06aef-3cda-4d11-81ca-e4b5134c7df5'), icon='mdi.island'),
    Topic('Terrain', TopicType.Worldbuilding, uuid.UUID('b2c2c6c4-3475-4219-bbdd-ddcee2ba4e41'), icon='mdi.terrain'),
    Topic('Planets', TopicType.Worldbuilding, uuid.UUID('d8c78689-2730-4127-9565-b6f75c98e362'), icon='ph.planet-fill'),
    Topic('Universum', TopicType.Worldbuilding, uuid.UUID('83d74ed5-f9e3-4a2d-aa18-d92632da9b78'),
          icon='mdi.atom-variant'),
    Topic('Moons', TopicType.Worldbuilding, uuid.UUID('ba829ae8-4563-42fe-9ffd-50737db617b6'), icon='fa5.moon'),
    Topic('Stars', TopicType.Worldbuilding, uuid.UUID('e45de6ad-07e5-4c78-8246-f715b6699c50'),
          icon='mdi.star-four-points'),
    Topic('Black holes', TopicType.Worldbuilding, uuid.UUID('b9720d11-51d9-4ccc-bee9-bbb2229c9d18'),
          icon='fa5s.circle'),
]
