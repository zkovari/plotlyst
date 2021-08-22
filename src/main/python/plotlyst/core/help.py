"""
Plotlyst
Copyright (C) 2021  Zsolt Kovari

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
from src.main.python.plotlyst.core.domain import enneagram_field

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
