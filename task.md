Overview

The goal of this task is to build a small service that can identify reference content vs commentary within a paragraph (HTML/XML-like structure), and return the same content with the appropriate tags applied.

What You’ll Do

Create an API endpoint (POST /parse-paragraph)
Accept a paragraph as input
Detect which parts are:
Reference
Commentary
Return the same paragraph with content wrapped in:
<reference>
<commentary>
Important Requirement

A key part of this task is preserving the original structure:

All existing tags (e.g, <span>, <i>, etc.) must remain unchanged
All attributes must be preserved exactly as they are
The output should be identical to the input, except for the added wrapper tags
Example

You’ll find examples in the attached document, including complex cases with nested tags and multiple attributes.

Time Expectation

This task should be delivered in 1 week, so on 03/04/2026. (3rd April 2026)

Submission

Please share:

A Git repository or ZIP file
A README with setup instructions and your approach
Sample request/response examples
Notes

We’re not expecting a perfect solution. We’re mainly interested in:

Your approach to solving the problem
Code quality and structure
How you handle edge cases and real-world complexity


Hello Kaio, hope you are doing well

 

I just wanted to clarify a couple of points about the task. My understanding is that distinguishing between commentary and references should be based on the semantics of the text only, rather than relying on tags. Is that correct?

Also, should commentary always be introduced by explicit phrases (e.g., “See also”), or should we infer it in other cases as well?




Hey Raul,

 

Yes, it should be based on semantics, not just the tags. However, please make sure to take the <span class="ins"> and <span class="del"> tags into account when processing content.

 

<span class="ins"> indicates inserted text (a track change), which should be included in your output.
<span class="del"> indicates deleted text, which should be ignored for semantic purposes but noted as part of the track change and included back in the response.
 

These two tags are specifically for tracking user edits, so we need to capture what was added or removed.

The other tags does not have any meaning for you at this moment, only the 2 tags mentioned above.

 

Regarding the commentary tag, please ensure your logic can infer commentary for other cases as well, since we may receive different types of commentary text within a paragraph.

 

I’m sending a few more examples for you, along with a sample response to show how we expect the paragraph to be returned.

Regards



Hi Raul,

 

We have analysed the project and identified the following points:

 

Which design pattern was implemented?
Output validation: the result is coming back with broken XML.
Some text is being tagged incorrectly. For example, “See” is included inside a <reference> tag. We need to properly infer all text and classify it correctly as either <reference> or <commentary>.
 

Example:

 

<reference>

  <i>See</i> Alejandro Linares, 'The Intervention of Constitutional Courts in International Investment Law: The Case of Colombia' (2021) 54 [1]

  <i>Cornell International Law Journal</i> 47.

</reference>

 

Please feel free to use any model if it helps you meet the requirements.




Hi Raul,

 

We have analysed the project and identified the following points:

 

Which design pattern was implemented?
Output validation: the result is coming back with broken XML.
Some text is being tagged incorrectly. For example, “See” is included inside a <reference> tag. We need to properly infer all text and classify it correctly as either <reference> or <commentary>.
 

Example:

 

<reference>

  <i>See</i> Alejandro Linares, 'The Intervention of Constitutional Courts in International Investment Law: The Case of Colombia' (2021) 54 [1]

  <i>Cornell International Law Journal</i> 47.

</reference>

 

Please feel free to use any model if it helps you meet the requirements.




TASK

Title
Reference vs Commentary Parser – Implementation, Fixes, and Improvements

Description
Implemented a service to classify paragraph content into <reference> and <commentary> while preserving XML structure exactly.

The solution follows a pipeline pattern:

Tokenizer – extracts semantic text and maintains position mapping to original XML.

Classifier – heuristic-based classification using citation patterns and linguistic signals.

Post-processing – splits mixed segments (e.g., “For discussion, see X”).

Wrapper – inserts tags without breaking XML structure.

Key Challenges & Fixes
1. Broken XML output

Root cause: naive string insertion and DOM mutation (lxml) breaking tag boundaries.

Fix: implemented text-aware wrapper using position tracking (text_idx vs xml_idx) to avoid inserting inside tags.

2. Incorrect segmentation (critical bug)

Issue: tokenizer split inside author names (e.g., J. C. Davis).

Fix: improved sentence boundary rules to:

prevent splitting on initials (J., J. C.)

avoid breaking citation flows

3. Incorrect classification of “See”

Issue: “See” included inside <reference> block.

Root cause: overly aggressive split using .search() (matched anywhere).

Fix: restrict splitting to leading triggers only using .match().

4. Mixed segment handling

Implemented logic to correctly split:

commentary → reference (For discussion, see X)

reference → trailing commentary (..., for further details)

Design Decisions
Avoided full DOM mutation (lxml) due to instability with partial text wrapping.

Chose position-based wrapping for deterministic and safe XML output.

Used heuristic classifier instead of ML for performance and explainability.

Current Output Guarantees
XML structure fully preserved

No broken or malformed tags

Accurate separation of:

narrative commentary

bibliographic references

Known Limitations / Next Steps
Edge cases with highly complex citation structures may require:

confidence scoring

optional ML fallback

Potential improvement:

smarter grouping of multi-author references

deeper NLP-based classification

Result
Stable API endpoint:

POST /parse-paragraph
Returns:

Valid XML

Correct semantic tagging

No structural mutations