
---

# ** Data Cleaning Notes: Handling Duplicate Reports After Merge**

During the data preparation stage, I identified a pattern of repeated rows in the merged dataset. These rows appeared to be duplicates because **all columns were identical**, except for one field — `service_key`.

### ** Key Observations**

* Each duplicated group shared the **same `report_id`**, which is supposed to be **unique for every report**.
* The only variation within the repeated rows was the **`service_key`**.
* For certain service types (e.g., **WLESS** and **HSE**), multiple service keys all mapped back to the **same service code** (e.g., WLESS had keys 1, 9, 18).
* This confirmed that these were not distinct records — they were simply repeated entries caused by redundant service key mappings.

### ** Action Taken**

To resolve this:

* I dropped duplicates **after merging** using `report_id` as the deduplication key.
* This ensured that **only one valid copy of each report** was kept and all artificial duplicates were removed.
* The cleaned dataset now contains a **unique row per report**, preventing double-counting in analysis and ensuring accurate reporting.

### ** Outcome**

The dataset is now:

* Clean and consistent
* Free from artificial duplication
* Ready for reliable analysis and reporting

---

