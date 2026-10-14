"""Definition answer grounding guard for v0.5.11.1.

Unknown definition questions must not be rescued solely by semantic-probe
agreement if the response fails to name the requested concept.
This is conservative lexical grounding, not truth verification.
"""
from interactive_unknown_learning_v0510 import concept_from

def definition_grounded(question,answer):
    concept=concept_from(question)
    if concept is None:
        return True,"not a definition question"
    if concept in answer:
        return True,"definition concept present"
    return False,f"definition concept absent: {concept}"
