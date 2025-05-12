We have been removing the promptType functionality from the code. We have archived files, edited code and we are now building and running tests to make sure things still work.

You need to activate the venv before running tests. For example:
cd /home/jem/development/prompt_manager && . venv/bin/activate && python -m unittest tests/test_composite_handling.py tests/test_prompt_service.py tests/test_unified_prompt.py

Please continue running and debugging the tests.

You are currently having an issue with recursion, and I think you are doing it wrong because you are trying to track recursion depth.

This is not how we should be handling recursion. We want to strictly disallow loops in inclusion. The process should work something like this:
* We find an inclusion in a file and when we start processing these inclusions we create a set of files included so far (let's call the set "inclusions"), and we add the current file to that set. We check the set to see if the file to be included is in inclusions, if it is we issue a warning, and continue processing the file looking to see if there are any other inclusions to be processed.
* If it's not in the inclusion set we call the file to be included to process it's own inclusions passing the inclusion set. It follows exactly the same process as described in the previous step.

At the point we should not need to worry about recursion depth because, at worst, we end up including every prompt file, but that will terminate because it is a finite set.

