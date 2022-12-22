## Contextual Knowledge Extraction from Dialogue
## Created by Thomas Belluci, AI Master student, 2022

_In partial fulfillment of the degree of MSc Artificial Intelligence at the Vrije Universiteit (VU), Amsterdam_

## Overview
In this repository you will find the code base for the MSc AI master project on contextual interpretation of user responses for dialogue systems.

## Annotation

To create the data for this project, short dialogues were sampled from three existing datasets: PersonaChat, DailyDialogs and Google Circa. These dialogues were manually annotated with ground-truth interpretations in the form of triples and perspectives and an Albert-based triple extractor was trained to learn to extract these triples.

**Note to annotators:** The annotation tool, instructions and revised annotation guidelines can be found in `src/annotation_tool`. The batches to be annotated are stored under `src/data_creation/batches`.
