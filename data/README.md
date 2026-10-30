# Data: Evidence and gap map of haematolymphoid tumours (AML and B-ALL/LBL)

| File | Source map | References |
| --- | --- | --- |
| `Report_AML.json` | Acute myeloid leukaemia (AML), including myeloid sarcoma | 1,255 |
| `Report_B-ALL.json` | Precursor B-cell neoplasms (B-ALL/LBL) | 839 |

Each file is an EPPI-Reviewer JSON export containing the result of the mapping process for one tumour group of the WCT EVI MAP project (AML or B-ALL/LBL). `CodeSets` holds the coding framework (Blue Book tumour hierarchy, tumour characteristics, study designs and levels of evidence); `References` holds one record per included study with its codes.

Fields kept per reference: `ItemId`, `OldItemId` (EPPI-Reviewer study identifier), `Title`, `ShortTitle`, `Authors`, `ParentTitle` (journal), `Year`, `Volume`, `Issue`, `Pages`, `DOI`, `URL`, `StandardNumber` (ISSN), `TypeName`, `QuickCitation`, `Abstract` (as retrieved from MEDLINE or Embase) and `Codes`. No full texts are included. All other fields of the original exports (comments, keywords, affiliations, reviewer account and status fields) were removed with `00_clean_eppi_export.py` in the repository root. This does not change any computed output.

Tumour group and tumour type names are reproduced verbatim from the WHO Classification of Tumours, 5th Edition, Volume 11: Haematolymphoid Tumours (WHO-HAEM5).

The data are made available with the permission of the International Agency for Research on Cancer (IARC).

## Licence

Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/

The abstracts are reproduced as published and remain under the copyright of their respective publishers; they are not covered by the CC BY 4.0 licence.
