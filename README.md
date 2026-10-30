# WCT EVI MAP scripts

Python scripts for generating the figures and tables of an evidence and gap map for acute myeloid leukaemia (AML) and precursor B-cell neoplasms (B-ALL/LBL), two groups of non-solid haematological malignancies classified in the  WHO Classification of Tumours, 5th Edition, Volume 11: Haematolymphoid Tumours (WHO-HAEM5).

The scripts were developed within the WCT EVI MAP project (Mapping the Evidence for the WHO Classification of Tumours: a Living Evidence Gap Map by Tumour Type), coordinated by the International Agency for Research on Cancer (IARC).

## Contents

| File | Role |
| --- | --- |
| `00_clean_eppi_export.py` | Optional. Produces the public copies of the EPPI-Reviewer exports in `data/` by removing fields not needed for the analysis. |
| `01_automated_coding_loe.py` | Step 1. Adds a Level of Evidence (LoE) code to every coded reference of one EPPI-Reviewer export and splits references with several characteristics into one record per characteristic. |
| `01_study_design_to_loe_HETP.json` | Lookup table used by step 1: characteristic and study design to LoE, following the Hierarchy of Research Evidence for Tumour Pathology (HETP). |
| `02_merge_json_files.py` | Step 2. Merges the LoE-coded files of all source maps of one Blue Book into one JSON, reconciling the code IDs of the separate EPPI-Reviewer reviews. |
| `03_egm_figures_and_tables.py` | Step 3. Generates all computed figures and tables from the merged JSON. |
| `egm_common.py` | Shared core imported by step 3: parsing, counting units, display order, colours and style. Not run on its own. |
| `data/` | Coding data of the Haematolymphoid evidence and gap map: one EPPI-Reviewer export each for the AML map and the B-ALL/LBL map. |

## Pipeline overview

```
EPPI-Reviewer JSON export (one per source map)
        |
        |  01_automated_coding_loe.py   (run once per export)
        v
<export>_loe.json (one per source map)
        |
        |  02_merge_json_files.py       (run once per Blue Book)
        v
Report_merged_loe.json
        |
        |  03_egm_figures_and_tables.py
        v
4_Figures/   5_Tables/   6_Supplemental_material/
```

Screening and coding were done in EPPI-Reviewer and the interactive maps were built with EPPI-Mapper. These scripts take over from the EPPI-Reviewer JSON export.

## Requirements

* Python 3.9 or later
* numpy, pandas and matplotlib (see `requirements.txt`)

Steps 1 and 2 use the Python standard library only. Tested with Python 3.10, numpy 2.2, pandas 2.3 and matplotlib 3.10.

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducing the publication

From the repository root, the following commands regenerate every computed figure and table of the AML and B-ALL/LBL publication from the data in `data/`. All outputs are written into `data/`.

```
python 01_automated_coding_loe.py data/Report_AML.json
python 01_automated_coding_loe.py data/Report_B-ALL.json
python 02_merge_json_files.py data
python 03_egm_figures_and_tables.py data/Report_merged_loe.json
```

The full run takes under a minute. The generated JSON files and output folders are excluded from version control.

## Usage

### Step 1: add levels of evidence

Run once for every EPPI-Reviewer export (one per source map, for example the AML map and the B-ALL/LBL map):

```
python 01_automated_coding_loe.py path/to/Report_AML.json
python 01_automated_coding_loe.py path/to/Report_B-ALL.json
```

Each run writes `<input name>_loe.json` next to its input. The script first checks that every reference has at least one characteristic, one study design and one tumour type coded; if not, it lists the affected titles and stops without writing output. Summary statistics (records per tumour type and characteristic, records before and after splitting, multi-coded records, systematic reviews) are printed to the terminal.

### Step 2: merge the source maps of one Blue Book

Folder mode merges every `*_loe.json` in a folder. The first file in alphabetical order is the primary, whose codeset becomes the canonical one:

```
python 02_merge_json_files.py path/to/haem_folder
```

Explicit mode sets the order yourself, primary first:

```
python 02_merge_json_files.py --files Report_AML_loe.json Report_B-ALL_loe.json --output Report_merged_loe.json
```

Without `--output`, the result is written as `Report_merged_loe.json` next to the inputs. References are concatenated without deduplication, and an integrity check confirms that every reference code resolves in the merged codeset.

### Step 3: figures and tables

```
python 03_egm_figures_and_tables.py path/to/Report_merged_loe.json
```

Options:

* `--output-dir DIR` writes the output folders under `DIR` instead of next to the JSON.
* `--only NAME [NAME ...]` rebuilds selected outputs only, for example `--only fig7_gap_matrix table1_details_of_egm`.

Available builder names: `table1_details_of_egm`, `table2_evidence_level_by_tumour_group`, `fig3_studies_per_year`, `fig4_study_designs`, `fig5_characteristics_by_loe`, `fig6_high_loe_heatmap`, `fig7_gap_matrix`, `figS5_characteristics_by_loe_by_group`, `figS6_tumour_type_by_loe_by_group`, `tableS9_S12_characteristics_by_loe`, `tableS10_S13_type_by_characteristic`, `tableS11_S14_type_by_loe`.

## Outputs

Every figure is saved as PNG (300 dpi) and PDF, together with a `_data.tsv` file holding the numbers it plots. Tables are tab-separated files, because some journals do not accept spreadsheet uploads. Output names follow the numbering of the AML and B-ALL/LBL publication.

| Output | Folder | Content |
| --- | --- | --- |
| Figure 3 | `4_Figures` | Studies per publication year, stacked by source map |
| Figure 4 | `4_Figures` | Studies per study design, stacked by source map |
| Figure 5 | `4_Figures` | Characteristics by LoE, all tumour types pooled |
| Figure 6 | `4_Figures` | Heatmap of the share of high-level evidence (P1 and P2) by source map and characteristic |
| Figure 7 | `4_Figures` | Gap classification matrix, tumour type by characteristic, all source maps combined |
| Table 1 | `5_Tables` | Details of the evidence and gap map per source map and in total |
| Table 2 | `5_Tables` | Evidence level bands per source map |
| Supplementary Figure S5 | `6_Supplemental_material` | Characteristics by LoE, one panel per source map (a AML, b B-ALL/LBL) |
| Supplementary Figure S6 | `6_Supplemental_material` | Tumour types by LoE, one panel per source map (a AML, b B-ALL/LBL) |
| Supplementary Tables S9, S12 | `6_Supplemental_material` | Characteristic by LoE, AML and B-ALL/LBL |
| Supplementary Tables S10, S13 | `6_Supplemental_material` | Tumour type by characteristic, AML and B-ALL/LBL |
| Supplementary Tables S11, S14 | `6_Supplemental_material` | Tumour type by LoE, AML and B-ALL/LBL |

The following items of the publication are not produced by these scripts, because they were made by the authors or come from project documents: Figure 1 (map screenshot), Figure 2 (PRISMA 2020 flow diagram), Supplementary Figures S1 to S4 (decision tree, screening decision flow diagram, screening progress in EPPI-Reviewer, PRISMA flow diagrams per tumour group) and Supplementary Tables S1 to S8 (tumour classification, characteristics, eligibility criteria, search strategies and the adapted HETP). The HETP of Supplementary Table S8 is used by the scripts as `01_study_design_to_loe_HETP.json`.

## Methods notes

### Levels of evidence

The LoE of a record is derived from its characteristic and study design using the HETP (Colling et al., 2024). The same study design can receive a different level depending on the characteristic, so the lookup table is keyed by characteristic first. Levels run from P1 (highest) to P5, plus Unclassifiable for designs the hierarchy does not rank for that characteristic. High-level evidence means P1 or P2, medium-level evidence P3 and low-level evidence P4 or P5.

### Source maps and tumour groups

Per group outputs are split by source map, i.e. by the search and map that produced the records, not by the tumour group of the codeset. For the Haematolymphoid Blue Book there are two source maps: AML, which combines the three AML codeset groups (AML with defining genetic abnormalities, AML defined by differentiation and myeloid sarcoma), and precursor B-cell neoplasms (B-ALL/LBL). The assignment is set in `SOURCE_MAP_OF_GROUP` in `egm_common.py`; every codeset group not listed there is its own source map.

### Counting units

One study can be coded for several characteristics and several tumour types, so three counting units are used and kept apart:

* **Unique studies**: one per EPPI-Reviewer study identifier (`OldItemId`) and source map. Used for Figures 3 and 4 and the study rows of Table 1.
* **Entries**: one per study and characteristic, i.e. one record after step 1. Used for Figures 5, 6 and S5, Tables 2, S9 and S12 and the entry rows of Table 1.
* **Tumour type records**: one per entry and tumour type it is coded for (fan-out counting). Used for Figures 7 and S6 and Tables S10, S11, S13 and S14.

The Total column of Table 1 sums the source maps, so a study coded in two maps is counted in both. The deduplicated count across maps, based on DOI, is printed to the terminal.

### Gap classification

Each cell of the gap matrix (one tumour type by one characteristic) is classified on its tumour type records:

| Category | Rule |
| --- | --- |
| Absolute gap | no records |
| Relative gap | 1 to 19 records, none at P1 or P2 |
| Synthesis gap | 20 or more records, none at P1 or P2 |
| Solid evidence | at least one record at P1 or P2 |

### Nomenclature

Tumour group and tumour type names are reproduced verbatim from the WHO Classification of Tumours as they appear in the coding data. Study design labels are anglicised at the display layer only (`STUDY_DESIGN_DISPLAY` in `egm_common.py`); the data are never edited.

## Input data

The `data/` folder holds the coding data behind the publication: `Report_AML.json` (1,255 references) and `Report_B-ALL.json` (839 references), exported from EPPI-Reviewer. The public copies keep the codes, the bibliographic details and the abstract of each study (retrieved from MEDLINE or Embase); comments, keywords, affiliations and reviewer account fields were removed with `00_clean_eppi_export.py`. No full texts are included. Running the pipeline on these copies gives exactly the same figures and tables as on the original exports. The data are made available with the permission of the International Agency for Research on Cancer (IARC) and are licensed under CC BY 4.0, see `data/README.md`.

The scripts expect the standard EPPI-Reviewer JSON export structure: a `CodeSets` list whose first codeset holds four top-level attributes (the Blue Book tumour hierarchy, `Characteristics`, `Study design` and `Level of Evidence (LoE)`), and a `References` list in which every reference carries its codes as `AttributeId` entries together with `Title`, `Year`, `DOI` and `OldItemId`. Characteristic and study design names must match the keys of `01_study_design_to_loe_HETP.json` exactly.

## Citation

If you use these scripts, please cite the software archive and the associated publication:

* WCT EVI MAP project. WCT EVI MAP scripts (version 1.0.0). Zenodo. doi: [to be added after the first Zenodo release]
* [Associated publication on the evidence and gap map of AML and B-ALL/LBL, to be added after publication]

Citation metadata are also provided in `CITATION.cff`.

### Reference

Colling R, Indave I, Del Aguila J, et al. A new hierarchy of research evidence for tumor pathology: a Delphi study to define levels of evidence in tumor pathology. Mod Pathol. 2024;37(1):100357.

## Licence

The code is released under the MIT Licence, see `LICENSE`. The data in `data/` are licensed under CC BY 4.0, except the abstracts, which remain under the copyright of their publishers.

## Funding

This work was carried out within the WCT EVI MAP project, funded by the European Union under the Horizon Europe programme (HORIZON-HLTH-2021-CARE-05, grant agreement No. 101057127). Views and opinions expressed are those of the authors only and do not necessarily reflect those of the European Union or the European Health and Digital Executive Agency. Neither the European Union nor the granting authority can be held responsible for them.

## Contact

For questions, please contact the corresponding author of the associated publication.
