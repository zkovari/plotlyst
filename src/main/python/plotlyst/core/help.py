"""
Plotlyst
Copyright (C) 2021-2023  Zsolt Kovari

This file is part of Plotlyst.

Plotlyst is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Plotlyst is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from dataclasses import dataclass
from typing import Dict, List

from src.main.python.plotlyst.core.domain import enneagram_field
from src.main.python.plotlyst.core.template import Role, protagonist_role, antagonist_role, major_role, secondary_role, \
    tertiary_role, \
    love_interest_role, supporter_role, adversary_role, contagonist_role, guide_role, confidant_role, sidekick_role, \
    foil_role, henchmen_role

# flake8: noqa
enneagram_help = {
    enneagram_field.selections[0].text: '''<html>Ethical type who wants to be good and right, and often seeks to improve the world.<ul>
    <li><b>Desire</b>: Being good, balanced, have integrity</li>
    <li><b>Fear</b>: Being incorrect, corrupt, evil</li>
    </ul>''',
    enneagram_field.selections[1].text: '''<html>Generous, attentive type who loves to help people and make their surrounding a better place.<ul>
    <li><b>Desire</b>: To be loved and appreciated
    <li><b>Fear</b>: Being unloved, unwanted
    </ul>''',
    enneagram_field.selections[2].text: '''<html>Success-oriented type who values their image and driven for achievements.<ul>
    <li><b>Desire</b>: Be valuable and worthwhile
    <li><b>Fear</b>: Being worthless
    </ul>''',
    enneagram_field.selections[3].text: '''<html>Creative, sensitive type who feels unique and authentic and seeks ways to express it.<ul>
    <li><b>Desire</b>: Express their individuality
    <li><b>Fear</b>: Having no identity or significance
    </ul>''',
    enneagram_field.selections[4].text: '''<html>Independent, perceptive type who seeks knowledge and often prefers privacy and time alone.<ul>
    <li><b>Desire</b>: Be competent
    <li><b>Fear</b>: Being useless, incompetent
    </ul>''',
    enneagram_field.selections[5].text: '''<html>Loyal, hard-working, cautious type who seeks safety and security.<ul>
    <li><b>Desire</b>: Have security and support
    <li><b>Fear</b>: Being vulnerable and unprepared
    </ul>''',
    enneagram_field.selections[6].text: '''<html>Spontaneous, enthusiastic type who seeks new experiences.<ul>
    <li><b>Desire</b>: Be stimulated, engaged, satisfied
    <li><b>Fear</b>: Being deprived
    </ul>''',
    enneagram_field.selections[7].text: '''<html>Dominating, confident type who seeks to be powerful and avoid relying on others.<ul>
    <li><b>Desire</b>: Be independent and in control
    <li><b>Fear</b>: Being vulnerable, controlled, harmed
    </ul>''',
    enneagram_field.selections[8].text: '''<html>Optimistic, adaptive type who seek to maintain peace and harmony.<ul>
    <li><b>Desire</b>: Internal peace, harmony
    <li><b>Fear</b>: Loss, separation
    </ul>'''

}

mbti_help = {'ISTJ': '''<html><h3>The Inspector</h3>
                Dependable and systematic types who enjoy working within clear systems and processes. Traditional, task-oriented and decisive.
             ''',
             'ISFJ': '''<html><h3>The Protector</h3>
             ISFJs are patient individuals who apply common sense and experience to solving problems for other people. They are responsible, loyal and traditional, enjoying serving the needs of others and providing practical help.
             ''',
             'ESTP': '''<html><h3>The Dynamo</h3>
             ESTPs motivate others by bringing energy into situations. They apply common sense and experience to problems, quickly analysing what is wrong and then fixing it, often in an inventive or resourceful way.
             ''',
             'ESFP': '''<html><h3>The Performer</h3>
             ESFP people tend to be adaptable, friendly, and talkative. They enjoy life and being around people. This personality type enjoys working with others and experiencing new situations.
             ''',
             'INFJ': '''<html><h3>The Counselor</h3>
             INFJs may come across as individualistic, private and perhaps mysterious to others, and may do their thinking in a vacuum, resulting in an unrealistic vision that is difficult to communicate.
             ''',
             'INTJ': '''<html><h3>The Mastermind</h3>
             INTJ people are often able to define a compelling, long-range vision, and can devise innovative solutions to complex problems.
             ''',
             'ENFP': '''<html><h3>The Champion</h3>
             Moving quickly from one project to another, ENFPs are willing to consider almost any possibility and often develop multiple solutions to a problem. Their energy is stimulated by new people and experiences.
             ''',
             'ENTP': '''<html><h3>The Visionary</h3>
             ENTPs solve problems creatively and are often innovative in their way of thinking, seeing connections and patterns within a system. They enjoy developing strategy and often spot and capitalise on new opportunities that present themselves.
             ''',
             'ISFP': '''<html><h3>The Composer</h3>
             ISFPs enjoy providing practical help or service to others, as well as bringing people together and facilitating and encouraging their cooperation.
             ''',
             'INFP': '''<html><h3>The Healer</h3>
             INFP people enjoy devising creative solutions to problems, making moral commitments to what they believe in. They enjoy helping others with their growth and inner development to reach their full potential.
             ''',
             'ESFJ': '''<html><h3>The Provider</h3>
             ESFJs tend to be sociable and outgoing, understanding what others need and expressing appreciation for their contributions. They collect the necessary facts to help them make a decision and enjoy setting up effective procedures.
             ''',
             'ENFJ': '''<html><h3>The Teacher</h3>
             ENFJs are able to get the most out of teams by working closely with them, and make decisions that respect and take into account the values of others. They tend to be adept at building consensus and inspiring others as leaders.
             ''',
             'ISTP': '''<html><h3>The Craftsperson</h3>
             ISTPs tend to enjoy learning and perfecting a craft through their patient application of skills. They can remain calm while managing a crisis, quickly deciding what needs to be done to solve the problem.
             ''',
             'INTP': '''<html><h3>The Architect</h3>
             INTP people think strategically and are able to build conceptual models to understand complex problems. They tend to adopt a detached and concise way of analysing the world, and often uncover new or innovative approaches.
             ''',
             'ESTJ': '''<html><h3>The Supervisor</h3>
             ESTJs drive themselves to reach their goal, organising people and resources in order to achieve it. They have an extensive network of contacts and are willing to make tough decisions when necessary. They tend to value competence highly.
             ''',
             'ENTJ': '''<html><h3>The Commander</h3>
             ENTJs see the big picture and think strategically about the future. They are able to efficiently organise people and resources in order to accomplish long-term goals, and tend to be comfortable with taking strong leadership over others.
             '''
             }

plot_value_help = """<html>When associated with scenes, such plot value can be charged <b style=color:#52b788;>positively</b> or 
<b style=color:#9d0208;>negatively</b>, thus depicting a 
character's shift between the value's positive and negative spectrum, e.g., Love vs. Hate.</html>"""

scene_disaster_outcome_help = """<html><head/><body><p>Scene ends with a <span style=" font-weight:600; color:#f4442e;">disaster</span>,
 so the agenda character's scene goal remains unachieved</p></body></html>"""

scene_trade_off_outcome_help = """<html><head/><body><p>Scene ends with a bittersweet <span style=" font-weight:600; color:#832161;">trade-off</span>,
 so the agenda character's scene goal is achieved but not without a price</p></body></html>"""

scene_resolution_outcome_help = """<html><head/><body><p>Scene ends with a <span style=" font-weight:600; color:#6ba368;">resolution</span>,
 so the agenda character's scene goal is achieved</p></body></html>"""

scene_motion_outcome_help = """<html><head/><body><p>Scene sets the story in motion without delivering any imminent disaster or resolution outcome</p></body></html>"""

mid_revision_scene_structure_help = """<html>This panel is recommended for <b>mid-revision</b> stage after the writer has already completed the first draft and implemented early, high-level developmental changes.
<br/>During mid-revision, the writer might refine scene structure to ensure tension, escalation, and reader engagement.
"""

home_page_welcome_text = """Plotlyst is an advanced writing software tailored for both aspiring and professional novelists.

It offers a range of tools to support various stages of novel writing, including outlining and planning, drafting, and early, mid, or late-stage revisions.

Not every tool aligns with every individual's writing process, and not all tools are universally suitable for all genres. Plotlyst is highly customizable, allowing you to choose and tailor the features that fit your specific preferences and needs.

Not every tool needs to be used right away. Several features prove most beneficial after the initial drafting phase.
"""

character_roles_description: Dict[Role, str] = {
    protagonist_role: """
    The central character around whom the story revolves.
    <br>They typically undergo personal growth, development, or transformation by the story's conclusion.
    <p>Protagonists often drive the narrative and face significant challenges, having the most at stake.
    <p>Note that the protagonist may not always have a point of view.
    """,
    antagonist_role: """
    The character who opposes the protagonist most, creating a central conflict in the story.
    <p>While often referred to as the villain, the antagonist is not necessarily an evil character.
    <p>Their opposition serves as a catalyst for the story's conflict, and they may have complex motives or goals that drive their actions.
    """,
    major_role: """
    Central character who plays a significant role in impacting the story.<br>They might undergo character development and changes themselves.
    <p>For major but more specific roles see protagonist and antagonist.
    """,
    secondary_role: """Important characters contributing to the story and major character development.
    <br>They may have their own subplots and character development but aren't the primary focus.
    <p>Subcategories include sidekick, love interest, guide, supporter/adversary, and contagonist.
    <p>If promoted, they become the deuteragonist - the second most important character role.
    """,
    tertiary_role: """
    Minor characters with limited appearance and impact in the story.
    <br>They may still serve specific functions such as providing information, kickstarting a plot, acting as red herrings, or enhancing the setting and atmosphere.
    <p>For special, antagonistic tertiary characters, see hecklers.
    """,

    love_interest_role: """Romance is in the air for the protagonist. In romance genre, this role could be promoted to a major one. In others, this role could be part of a subplot in which case it shall remain a secondary character. """,

    adversary_role: """
    Characters who oppose the protagonist. While not as central as the antagonist, they still present challenges and tension to the protagonist.
    <p>For a more formidable opposition, see contagonist.
    <p>For lesser, minor, adversaries, consider hecklers.
    """,

    supporter_role: """
    A secondary character type providing support to the protagonist in their journey. They may not fit into more specialized roles like guide, sidekick, or confidant, but they are considered allies.
    <p>Subcategories: Sidekick, Confidant, Guide
    """,
    guide_role: """
    Often referred to as a mentor, this secondary role typically imparts valuable lessons to the protagonist.
    <br>They may share wisdom, knowledge, skills, or provide guidance and direction, be it physical, spiritual, or psychological.
    """,
    confidant_role: """
    Serves as a trusted ally and emotional support, with whom the protagonist can share personal thoughts and feelings.
    <p>Often overlaps with sidekicks, mentors, or love interests.
    <p>This role often implies a deeper personal connection to the protagonist compared to sidekicks.
    """,
    sidekick_role: """
    A loyal companion and supporter to the protagonist, actively participating in their adventures.
    <p>May have a strong, dynamic relationship with the protagonist, often bringing unique skills or qualities that complement the protagonist's abilities.
    """,

    contagonist_role: """The second most important opposition after the antagonist. Often, the contagonist will sway the protagonist from their desire.
    They might unite with the antagonist, although their gole can be different.""",
    foil_role: """A mirror character who represents the opposite of the protagonist in terms of personality, appearance, worldview, or values. Not necessarily an antagonistic character but could be.
A foil role can help to contrast the protagonist making them a multi-dimensional character. Also, a foil might represent a different facade of the theme, thus contrasting or empowering the protagonist's version of the truth.""",
    henchmen_role: """Minor characters who oppose the protagonist and their supporting cast. They bring in smaller conflicts so they are less important than any other antagonistic roles.
    Hecklers often come in greater numbers."""
}


@dataclass
class CharacterRoleExample:
    name: str
    title: str
    icon: str = ''
    display_title: bool = True


def character_role_examples(role: Role) -> List[CharacterRoleExample]:
    if role == protagonist_role:
        return [
            CharacterRoleExample('Katniss', 'Hunger Games', 'mdi6.bow-arrow'),
            CharacterRoleExample('Harry Potter', 'Harry Potter', 'ei.magic', False),
        ]

    return []
