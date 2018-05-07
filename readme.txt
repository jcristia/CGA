The big change from the previous version:
The feature count functionality was taking way too long to process. To separate out by mpa and ecosection it requires reseting the cursor many times - almost as many times as there are features, so for datasets with 19,000 features, this becomes very slow.

The previous version maintains this code. The version before the previous version has the code where it only splits out by mpa. If it ends up where I still need feature count, then I should revert back to the verison from two versions ago.