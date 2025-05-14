import dataclasses
from random import random, shuffle
import re

@dataclasses.dataclass
class TrainingRequirement:
    probability: float
    description: str

    tags: list[str]

requirement_pool = [
    TrainingRequirement(
        probability=0.25,
        description="Today will be a pain day. He will be connected with the clamshells/Coyote while training. "
                    "He must gradually reach level 50 by the time he is finished.",
        tags=["pain", "hood"],
    ),

    TrainingRequirement(
        probability=0.1,
        description="He will be kneeling on the floor.",
        tags=["position"],
    ),
    TrainingRequirement(
        probability=0.1,
        description="He will be kneeling on the kneeling bench.",
        tags=["position"],
    ),
    TrainingRequirement(
        probability=0.05,
        description="He will have his forehead on the ground.",
        tags=["position"],
    ),
    TrainingRequirement(
        probability=0.1,
        description="He will be standing in the middle of the room.",
        tags=["position"],
    ),
    TrainingRequirement(
        probability=0.1,
        description="He will be standing in the bathtub.",
        tags=["position"],
    ),

    TrainingRequirement(
        probability=0.2,
        description="He will only have 75 seconds to get close to orgasm.",
        tags=["speed"],
    ),
    TrainingRequirement(
        probability=0.1,
        description="He will only have 60 seconds to get close to orgasm.",
        tags=["speed"],
    ),

    TrainingRequirement(
        probability=0.5,
        description="He will use the Hitachi.",
        tags=["method"],
    ),

    meds_reqmt := TrainingRequirement(
        probability=0.8,
        description="He will take meds ahead of time if they've arrived.",
        tags=["meds"],
    ),

    TrainingRequirement(
        probability=0.3,
        description="He will wear the metal anal plug.",
        tags=["anal"],
    ),

    TrainingRequirement(
        probability=0.1,
        description="He will be hooded.",
        tags=["hood"],
    ),
]

def requirements_strings():
    shuffle(requirement_pool)

    chosen_requirements = [meds_reqmt]
    tags_so_far = set(meds_reqmt.tags)
    probability_modifier = 1.0
    for requirement in requirement_pool:
        if random() <= requirement.probability*probability_modifier and not tags_so_far & set(requirement.tags):
            chosen_requirements.append(requirement)
            probability_modifier *= 0.7
            tags_so_far = tags_so_far | set(requirement.tags)

    if not chosen_requirements:
        me_requirements_str = "  There are no special requirements."
    else:
        descriptions = [f" * {requirement.description}" for requirement in chosen_requirements]
        me_requirements_str = "\n".join(descriptions)


    drk_requirements_str = me_requirements_str

    for he, you in [("he is", "you are"), ("he", "you"), ("his", "your")]:
        drk_requirements_str = re.sub(f"\\b{he}\\b", you, drk_requirements_str)
        he, you = he.replace("h", "H"), you.replace("y", "Y")
        drk_requirements_str = re.sub(f"\\b{he}\\b", you, drk_requirements_str)

    return me_requirements_str, drk_requirements_str

