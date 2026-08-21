# A Typology of Decision-Making Tasks for Visualization

Source: Brumar, Molnar, Appleby, Potter, Chang. "A Typology of Decision-Making Tasks for Visualization." IEEE TVCG 31(10), October 2025. The source paper PDF is not bundled.

## Motivation

Many visualization task typologies describe low-level analytical operations rather than the larger decision problem. This typology describes decision support through three composable tasks: CHOOSE, ACTIVATE, and CREATE.

## Base entities

- **Options**: information entities being evaluated.
- **Features**: characteristics of options.
- **Criteria**: preferences or standards applied to features.

## CHOOSE

Assess a set of options and return the top or best $k$. Evaluation is dependent: whether an option is returned depends on comparison with other options. CHOOSE guarantees quantity but not absolute quality. Criteria can inform comparison but are not required.

## ACTIVATE

Evaluate options independently against a threshold and return those meeting it. ACTIVATE guarantees that returned options meet the criterion but does not guarantee how many options will be returned. Thresholds may be flexible rather than perfectly crisp.

## CREATE

Assemble, synthesize, or generate new information. CREATE can produce new options, new or modified features, or an output unlike the input. It guarantees neither quality nor quantity and often feeds a later CHOOSE or ACTIVATE step.

## Composability

The tasks can be hierarchical and iterative. A CREATE task can generate criteria for a later ACTIVATE task, an ACTIVATE filter can feed a CHOOSE ranking, and any task can be decomposed into smaller decision tasks.

## Key distinctions

- CHOOSE uses relative or dependent comparison; ACTIVATE uses independent thresholding.
- Task type is determined by the evaluation mechanism, not by broad user intent or UI interaction.
- CREATE represents meaningful synthesis or generation, not merely loading or transforming data mechanically.

## Design relevance

The typology gives visualization designers and domain experts language for decision-support requirements above raw clicks and filters but below a complete domain decision document.
