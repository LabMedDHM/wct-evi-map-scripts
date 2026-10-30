"""
01_automated_coding_loe.py
==========================
Step 1 of the WCT EVI MAP pipeline. Adds a Level of Evidence (LoE) code to
each reference in one EPPI-Reviewer coding JSON export and splits references
that carry more than one tumour characteristic into one record per
characteristic.

Run this once per source map (one search and one map, for example the AML
map or the B-ALL/LBL map of the Haematolymphoid Blue Book). The resulting
*_loe.json files are combined by 02_merge_json_files.py.

Background
----------
Each reference in the EPPI-Reviewer JSON export is coded with one or more
tumour types, one or more characteristics (for example Histopathology or
Prognosis) and a study design. The LoE is not stored in the export. It is
derived from the combination of characteristic and study design using the
Hierarchy of Research Evidence for Tumour Pathology (HETP; Colling et al.,
Modern Pathology 2024), encoded as a lookup table in
01_study_design_to_loe_HETP.json. The same study design can map to a
different LoE depending on the characteristic, which is why the lookup is
keyed by characteristic first.

Processing steps
----------------
1. Consistency check: every reference must have at least one characteristic,
   one study design and one tumour type coded. If any reference fails, the
   offending titles are printed and the script stops without writing output.
2. References with N characteristics are duplicated into N records, each
   retaining only one characteristic code.
3. For each record the LoE is looked up from (characteristic, study design)
   and appended as a code. Every code receives its human-readable name in
   the AdditionalText field.
4. Records are renumbered consecutively (ItemId) and written to a new file
   next to the input, with the suffix _loe.json. The original EPPI-Reviewer
   study identifier (OldItemId) is kept unchanged and is used downstream to
   identify unique studies.
5. A check confirms that no reference was lost or added by the split, then
   summary statistics are printed to the terminal: counts per tumour type,
   characteristic and study design; record totals before and after the
   split; the number of multi-coded records; and the number of systematic
   reviews.

Usage
-----
    python 01_automated_coding_loe.py <path_to_eppi_export.json>

Arguments
---------
    path_to_eppi_export.json : EPPI-Reviewer JSON export of one source map.

Output
------
    <input name>_loe.json, written next to the input file.

The lookup file 01_study_design_to_loe_HETP.json must reside in the same
directory as this script. Its keys must match the characteristic and study
design names in the EPPI-Reviewer codeset exactly, and its values must match
the names of the LoE codes (Level P1 to Level P5, Unclassifiable).
"""

import json
import os
import sys

REFS = "References"
CODES = "Codes"
CODE_SETS = "CodeSets"
ATTR = "Attributes"
ATTR_LIST = "AttributesList"
ATTR_ID = "AttributeId"
ATTR_NAME = "AttributeName"
ATTR_TYPE = "AttributeType"
ADD_TEXT = "AdditionalText"
CHARACTERISTICS = "Characteristics"
STUDY_DESIGN = "Study design"
LEVEL_EVIDENCE = "Levels of Evidence"
DEFAULT_TUMOUR = "Default Tumour"
TITLE = "Title"
SELECTABLE = "selectable"


def print_error_msg(error_msg: str) -> None:
    """Print a coloured (red) error message to the command line.

    Args:
        error_msg (`str`): Error message.
    """
    print(f"\033[91m{error_msg}\033[0m")


def replace_all(unformatted_str: str, characters: list) -> str:
    """Remove all the listed characters from the string.

    Args:
        unformatted_str (`str`): Unformatted string.
        characters (`list`): Characters to be removed.

    Returns:
        `str`: Formatted string.
    """
    formatted_str = unformatted_str
    for char in characters:
        formatted_str = formatted_str.replace(char, "")
    return formatted_str


def valid_json_path(json_path: str) -> bool:
    """Check if the given path represents an existing json-file.

    Args:
        json_path (`str`): Path to a json file.

    Returns:
        `bool`: Whether the specified json-path exists.
    """

    if (
        os.path.exists(json_path)
        and os.path.isfile(json_path)
        and json_path.endswith(".json")
    ):
        return True

    print_error_msg(f"Error: Specified path is invalid {json_path}!")
    return False


def read_json_content(json_path: str) -> dict:
    """Read the data from a json-file.

    Args:
        json_path (`str`): Path to the json-file.

    Returns:
        `dict`: Content of the json-file.
    """

    json_content = {}
    with open(json_path, "r") as json_file:
        json_content = json.load(json_file)
    return json_content


def write_json_content(json_path: str, content: dict) -> None:
    """Write the data to a json-file.

    Args:
        json_path (`str`): Path to the json-file.
        content (`dict`): Content of the json-file.
    """

    with open(json_path, "w") as json_file:
        json.dump(content, json_file, indent=4)


def find_selectable_attributes(data, selectable_items: dict) -> None:
    """Recursively collect every codeset attribute whose AttributeType starts
    with 'selectable', i.e. the codes a reviewer can tick. Recursion stops at
    a selectable node, so for the tumour axis this returns the tumour types
    and not the tumour groups above them.

    Args:
        data (`dict`/`list`): Parent list or dict to start searching.
        selectable_items (`dict`): Attribute IDs and names of all items
        found with AttributeType selectable.

    """
    if isinstance(data, dict):
        attr_type = data.get(ATTR_TYPE)
        if attr_type and attr_type.lower().startswith(SELECTABLE):
            if ATTR_ID in data.keys() and ATTR_NAME in data.keys():
                selectable_items[data[ATTR_ID]] = data[ATTR_NAME]
        else:
            for value in data.values():
                find_selectable_attributes(value, selectable_items)
    elif isinstance(data, list):
        for item in data:
            find_selectable_attributes(item, selectable_items)


def get_tumour_types(wp_content: dict) -> list:
    """Get all tumour types from the codeset. The tumour axis is the first
    top-level attribute that is neither Characteristics, Study design nor the
    LoE axis (the Blue Book node), and its selectable descendants are the
    tumour types.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.

    Returns:
        `list`: All tumour types found, if any.
    """
    tumour_types = []
    selectable_items = {}
    for attr_list_elem in wp_content["CodeSets"][0]["Attributes"]["AttributesList"]:
        set_attr_name = attr_list_elem["AttributeName"]
        if (
            "Characteristics" != set_attr_name
            and "Study design" != set_attr_name
            and "LoE" not in set_attr_name
        ):
            find_selectable_attributes(attr_list_elem, selectable_items)
            tumour_types = list(selectable_items.values())
            break
    return tumour_types


def get_code_sets(wp_content: dict):
    """Map every AttributeId in the codeset to its AttributeName.

    The codeset is read to a fixed depth: the children of each top-level axis
    (characteristics, study designs, LoE bands and tumour groups) and their
    children (tumour types). This matches the WCT EVI MAP codeset structure
    Blue Book > tumour group > tumour type. Deeper nesting would not be read.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.

    Returns:
        `dict`: AttributeId -> AttributeName (whitespace stripped).
    """

    code_sets = {}
    for attr1 in wp_content[CODE_SETS][0][ATTR][ATTR_LIST]:
        for attr2 in attr1[ATTR][ATTR_LIST]:
            if ATTR in attr2.keys() and ATTR_LIST in attr2[ATTR]:
                for attr3 in attr2[ATTR][ATTR_LIST]:
                    code_sets[attr3[ATTR_ID]] = attr3[ATTR_NAME].strip()
            code_sets[attr2[ATTR_ID]] = attr2[ATTR_NAME].strip()
    return code_sets


def get_wp_template(wp_content: dict) -> dict:
    """Build the output skeleton: the input CodeSets and an empty References
    list that is filled with the split and LoE-coded records.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.

    Returns:
        `dict`: {"CodeSets": <copy of input CodeSets>, "References": []}.
    """

    wp_template = {CODE_SETS: [], REFS: []}
    assert CODE_SETS in wp_content.keys(), "Expect " + CODE_SETS + " as key in WP dict!"
    wp_template[CODE_SETS] = wp_content[CODE_SETS].copy()
    return wp_template


def get_reference_codes(reference: dict) -> list:
    """Get all the codes of the given reference as list of numbers.

    Args:
        reference (`dict`): Reference which holds data for a study.

    Returns:
        `list`: Numbers representing the codes found.
    """

    return [code[ATTR_ID] for code in reference[CODES]]


def get_study_design_and_level(
    ref_code_translations: list, characteristic_info: dict
) -> tuple:
    """Get the study design of a reference and its LoE for one characteristic.

    Args:
        ref_code_translations (`list`): List of translated codes of
        the reference entry.
        characteristic_info (`dict`): HETP lookup for one characteristic,
        study design -> LoE.

    Returns:
        `tuple`: (study design, LoE) as strings, or ("", "") if the reference
        carries no study design listed for this characteristic.
    """

    for code_translation in ref_code_translations:
        if code_translation in characteristic_info.keys():
            return code_translation, characteristic_info[code_translation]

    return "", ""


def get_current_tumour_types(ref_codes: list, tumour_types: list) -> list:
    """Return the tumour types a reference is coded for, read from the
    AdditionalText of its codes (filled by add_text_to_codes).

    Args:
        ref_codes (`list`): Codes of the reference.
        tumour_types (`list`): List of all tumour types.

    Returns:
        `list`: Tumour types found, or an empty list.
    """

    tumour_types_found = []
    for code in ref_codes:
        add_text = code[ADD_TEXT]
        if add_text in tumour_types:
            tumour_types_found.append(add_text)
    return tumour_types_found


def clean_up_characteristics(
    reference: dict, curr_characteristic: str, characteristics: list, code_sets: dict
) -> None:
    """Remove all characteristic codes from a reference except the current one.

    Args:
        reference (`dict`): Given reference entry.
        curr_characteristic (`str`): Current characteristic.
        characteristics (`list`): All possible characteristic.
        code_sets (`dict`): Dictionary containing code and description.
    """

    clean_codes = []
    unneeded_characteristic_codes = [
        code
        for code, code_description in code_sets.items()
        if code_description in characteristics
        and code_description != curr_characteristic
    ]

    for code in reference[CODES]:
        if code[ATTR_ID] not in unneeded_characteristic_codes:
            clean_codes.append(code)
        else:
            print(
                f"\t\t\tRemoving code: {code[ATTR_ID]} -> Description: {code_sets[code[ATTR_ID]]}"
            )

    reference[CODES] = clean_codes


def add_level_code(codes: list, code_sets: dict, level_evidence: str) -> None:
    """Append the code for the given LoE band to a reference's codes.

    Args:
        codes (`list`): Current codes of the reference.
        code_sets (`dict`): Dictionary containing code and description.
        level_evidence (`str`): Level of evidence.
    """

    level_code = 0
    for code, code_description in code_sets.items():
        if code_description == level_evidence:
            level_code = code
    assert (
        level_code != 0
    ), f"Couldn't find level code for LOE = '{level_evidence}' in code_sets = {code_sets}"

    code_template = {
        ATTR_ID: level_code,
        ADD_TEXT: "",
        "ArmId": 0,
        "ArmTitle": "",
        "ItemAttributeFullTextDetails": [],
    }
    print(
        "\t\tAdd "
        + LEVEL_EVIDENCE
        + f" Code: {level_code} -> Description: {level_evidence}"
    )
    codes.append(code_template)


def add_text_to_codes(codes: list, code_sets: dict) -> None:
    """Write each code's human-readable name into its AdditionalText field.

    Args:
        codes (`list`): Current codes of the reference.
        code_sets (`dict`): Dictionary containing code and description.
    """
    for code in codes:
        if (
            ADD_TEXT in code.keys()
            and ATTR_ID in code.keys()
            and code[ATTR_ID] in code_sets.keys()
        ):
            code[ADD_TEXT] = code_sets[code[ATTR_ID]]


def print_statistics(wp_content: dict, tumour_types: list) -> None:
    """Print, for each tumour type, the number of records per characteristic
    and per study design (counted after splitting).

    Args:
        wp_content (`dict`): LoE-coded content.
        tumour_types (`list`): List of all tumour types.
    """

    tumour_stats = {
        tumour_type: {CHARACTERISTICS: {}, STUDY_DESIGN: {}}
        for tumour_type in tumour_types
    }
    tumour_stats[DEFAULT_TUMOUR] = {}

    for reference in wp_content[REFS]:
        curr_tumour_types = get_current_tumour_types(reference[CODES], tumour_types)
        curr_study_design = reference[STUDY_DESIGN]
        curr_characteristic = reference[CHARACTERISTICS]

        for curr_tumour_type in curr_tumour_types:
            curr_tumour_stats = tumour_stats[curr_tumour_type]

            if curr_study_design not in curr_tumour_stats[STUDY_DESIGN].keys():
                curr_tumour_stats[STUDY_DESIGN][curr_study_design] = 1
            else:
                curr_tumour_stats[STUDY_DESIGN][curr_study_design] += 1

            if curr_characteristic not in curr_tumour_stats[CHARACTERISTICS].keys():
                curr_tumour_stats[CHARACTERISTICS][curr_characteristic] = 1
            else:
                curr_tumour_stats[CHARACTERISTICS][curr_characteristic] += 1

    print(
        f"\n{150*'='}\n Statistics for each Tumour type:\n"
        f"{json.dumps(tumour_stats, indent=4)}"
    )


def count_presplit_multiples(
    wp_content: dict, code_sets: dict, tumour_types: list, characteristics: list
) -> tuple[int, int, int, int]:
    """Count, on the original export (before splitting), how many records
    have multiple tumour types and how many have multiple tumour characteristics.
    Also count, on the same data, how many unique records are affected by
    either condition (each record counted once even if both conditions hold)
    and how many records are coded as Systematic Review.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.
        code_sets (`dict`): Mapping from code ID to description.
        tumour_types (`list`): All tumour types detected in the export.
        characteristics (`list`): All tumour characteristics (keys of study_design_to_level).

    Returns:
        `tuple[int, int, int, int]`: (records_with_multiple_tumour_types,
        records_with_multiple_characteristics,
        records_with_multiple_tumour_types_or_characteristics,
        records_coded_as_systematic_review)
    """
    tumour_types_set = set(tumour_types)
    characteristics_set = set(characteristics)
    systematic_review_label = "Systematic Review"

    multi_tumour_count = 0
    multi_characteristics_count = 0
    multi_any_count = 0
    systematic_review_count = 0

    for reference in wp_content[REFS]:
        # Translate reference code IDs -> descriptive strings
        ref_codes = get_reference_codes(reference)
        translations = {code_sets[c] for c in ref_codes if c in code_sets}

        num_tumours = len(tumour_types_set.intersection(translations))
        num_characteristics = len(characteristics_set.intersection(translations))

        has_multi_tumour = num_tumours > 1
        has_multi_characteristics = num_characteristics > 1

        if has_multi_tumour:
            multi_tumour_count += 1
        if has_multi_characteristics:
            multi_characteristics_count += 1
        if has_multi_tumour or has_multi_characteristics:
            multi_any_count += 1
        if systematic_review_label in translations:
            systematic_review_count += 1

    return (
        multi_tumour_count,
        multi_characteristics_count,
        multi_any_count,
        systematic_review_count,
    )


def check_coding_consistency(
    wp_content: dict, study_design_to_level: dict, tumour_types: list, code_sets: dict
) -> bool:
    """Check that every reference has at least one characteristic, one study
    design and one tumour type coded. Offending titles are printed.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.
        study_design_to_level (`dict`): Dictionary containing characteristics and
        their corresponding study designs and level of evidence.
        tumour_types (`list`): List of all tumour types.
        code_sets (`dict`): Dictionary containing code and description.

    Returns:
        `bool`: Whether the coded data is consistent.
    """

    characteristics = set(study_design_to_level.keys())
    study_designs = {
        design
        for design_dict in study_design_to_level.values()
        for design in design_dict
    }
    tumour_types = set(tumour_types)

    is_consistent = True
    for reference in wp_content[REFS]:
        ref_codes = get_reference_codes(reference)
        ref_code_translations = {
            code_sets[code] for code in ref_codes if code in code_sets.keys()
        }
        check_msg = ""
        if not characteristics.intersection(ref_code_translations):
            check_msg += "\t\t-> No characteristic found in " + CODE_SETS + "\n"
        if not study_designs.intersection(ref_code_translations):
            check_msg += "\t\t-> No study design found in " + CODE_SETS + "\n"
        if not tumour_types.intersection(ref_code_translations):
            check_msg += "\t\t-> No tumour type found in " + CODE_SETS + "\n"

        # Print error message and set flag, if any inconsistency was found
        if check_msg:
            print(f"\tChecking reference: {TITLE} = {reference[TITLE]}")
            print_error_msg(check_msg)
            is_consistent = False

    return is_consistent


def check_modification_consistency(wp_content: dict, new_wp_content: dict) -> bool:
    """Confirm that splitting neither lost nor added a reference, by
    comparing the sets of titles before and after.

    Args:
        wp_content (`dict`): Content of the EPPI-Reviewer JSON export.
        new_wp_content (`dict`): LoE-coded content.

    Returns:
        `bool`: Whether modifications are consistent.
    """
    titles = {ref[TITLE] for ref in wp_content[REFS]}
    new_titles = {ref[TITLE] for ref in new_wp_content[REFS]}

    if titles == new_titles:
        return True

    titles_appeared = new_titles - titles
    if titles_appeared:
        print_error_msg(
            f"{len(titles_appeared)} references appear only in the extended "
            f"json-file:\n titles = {titles_appeared}"
        )
    titles_disappeared = titles - new_titles
    if titles_disappeared:
        print_error_msg(
            f"{len(titles_disappeared)} references disappear in the extended "
            f"json-file:\n titles = {titles_disappeared}"
        )
    return False


def get_characteristics_loe_count(
    wp_content: dict,
    tumour_type: str,
    study_design_to_level: dict,
    characteristics: list,
    levels_evidence: list,
) -> dict:
    """Count records per characteristic and LoE for one tumour type.

    Not called by main(); kept as a helper for interactive checks.

    Args:
        wp_content (`dict`): LoE-coded content.
        tumour_type (`str`): Tumour type to count.
        study_design_to_level (`dict`): HETP lookup (unused, kept for
        signature compatibility).
        characteristics (`list`): Characteristic names.
        levels_evidence (`list`): LoE band names.

    Returns:
        `dict`: characteristic -> {LoE: count}.
    """
    common_elements = lambda list1, list2: [
        element for element in list1 if element in list2
    ]

    characteristics_loe_count = {
        char: {loe: 0 for loe in levels_evidence} for char in characteristics
    }

    for reference in wp_content[REFS]:
        codes_texts = [code[ADD_TEXT] for code in reference[CODES]]
        if tumour_type not in codes_texts:
            continue

        curr_characteristics = common_elements(characteristics, codes_texts)
        curr_levels_evidence = common_elements(levels_evidence, codes_texts)
        if len(curr_characteristics) != 1 or len(curr_levels_evidence) != 1:
            print_error_msg(
                "Expect exactly one characteristic and LOE for each reference:\n"
                f"\tcharacteristics = {curr_characteristics}\n"
                f"\tlevel_evidence  = {curr_levels_evidence}\n"
            )
            continue

        curr_characteristic = curr_characteristics[0]
        curr_level_evidence = curr_levels_evidence[0]
        characteristics_loe_count[curr_characteristic][curr_level_evidence] += 1

    return characteristics_loe_count


def extend_reference(
    reference: dict, study_design_to_level: dict, code_sets: dict, characteristics: list
) -> list:
    """Split one reference into one record per characteristic and add the
    LoE code to each record.

    Args:
        reference (`dict`): Current reference.
        study_design_to_level (`dict`): Dictionary containing characteristics and
        their corresponding study designs and level of evidence.
        code_sets (`dict`): Dictionary containing code and description.
        characteristics (`list`): All possible characteristic.

    Returns:
        `list`: A list of references. Each reference represents the incoming one,
        but only referring to one characteristic.
        The list will contain N elements for a study with N characteristics.
    """

    ref_codes = get_reference_codes(reference)
    ref_code_translations = [
        code_sets[code] for code in ref_codes if code in code_sets.keys()
    ]
    curr_characteristics = [
        code_translation
        for code_translation in ref_code_translations
        if code_translation in characteristics
    ]
    print(f"\tReference characteristics: {curr_characteristics}")
    new_references = []
    for curr_characteristic in curr_characteristics:
        new_reference = reference.copy()
        study_design, level_evidence = get_study_design_and_level(
            ref_code_translations, study_design_to_level[curr_characteristic]
        )
        new_reference[CHARACTERISTICS] = curr_characteristic
        new_reference[STUDY_DESIGN] = study_design
        new_reference[LEVEL_EVIDENCE] = level_evidence

        print(
            f"\t\tCharacteristic: {curr_characteristic}\n"
            + f"\t\tStudy Design: {study_design}\n"
            + f"\t\tLevel Of Evidence: {level_evidence}"
        )

        clean_up_characteristics(
            new_reference, curr_characteristic, characteristics, code_sets
        )
        add_level_code(new_reference[CODES], code_sets, level_evidence)
        add_text_to_codes(new_reference[CODES], code_sets)

        new_references.append(new_reference)

    return new_references


def main(wp_path: str, study_design_to_level_path: str) -> None:
    """Run step 1 on one EPPI-Reviewer export: check consistency, split each
    reference into one record per characteristic, add the LoE code, write
    <input>_loe.json and print summary statistics.

    Args:
        wp_path (`str`): Path to the EPPI-Reviewer JSON export.
        study_design_to_level_path (`str`): Path to the HETP lookup JSON.
    """

    wp_content = read_json_content(wp_path)
    study_design_to_level = read_json_content(study_design_to_level_path)
    characteristics = list(study_design_to_level.keys())
    code_sets = get_code_sets(wp_content)
    tumour_types = get_tumour_types(wp_content)

    if not check_coding_consistency(
        wp_content, study_design_to_level, tumour_types, code_sets
    ):
        print_error_msg("=> Consistency check failed, stopping!")
        return

    new_wp_content = get_wp_template(wp_content)
    curr_id = 0
    for reference in wp_content[REFS]:
        print(f"{150*'='}\nExtending reference: Title = {reference['Title']}")
        new_references = extend_reference(
            reference, study_design_to_level, code_sets, characteristics
        )
        for new_reference in new_references:
            new_reference["ItemId"] = curr_id
            new_reference["EPPI-Revier ID"] = curr_id
            new_wp_content[REFS].append(new_reference)
            curr_id += 1

    write_json_content(wp_path.replace(".json", "_loe.json"), new_wp_content)

    if not check_modification_consistency(wp_content, new_wp_content):
        return

    print_statistics(new_wp_content, tumour_types)

    # Total reference counts before and after LoE-splitting
    pre_split_total = len(wp_content[REFS])
    post_split_total = len(new_wp_content[REFS])
    added_by_split = post_split_total - pre_split_total
    print(f"\n{150*'='}\nReference counts:")
    print(f"References before adding LoE (pre-splitting):  {pre_split_total}")
    print(f"References after adding LoE (post-splitting):  {post_split_total}")
    print(f"Additional rows produced by splitting:         {added_by_split}\n")

    # Count records that (pre-splitting) have multiple tumour types / characteristics
    (
        multi_tumour_count,
        multi_characteristics_count,
        multi_any_count,
        systematic_review_count,
    ) = count_presplit_multiples(
        wp_content, code_sets, tumour_types, characteristics
    )
    multi_any_pct = (
        round(100 * multi_any_count / pre_split_total, 2) if pre_split_total else 0.0
    )
    systematic_review_pct = (
        round(100 * systematic_review_count / pre_split_total, 2)
        if pre_split_total
        else 0.0
    )
    print(f"\n{150*'='}\nPre-split counts:")
    if multi_tumour_count == 0 and multi_characteristics_count == 0:
        print("No records with multiple tumour types or characteristics found.\n")
    else:
        print(f"Records with multiple tumour types: {multi_tumour_count}")
        print(f"Records with multiple characteristics: {multi_characteristics_count}")
        print(
            "Records with multiple tumour types and/or characteristics "
            f"(each record counted once): {multi_any_count} "
            f"({multi_any_pct:.2f}% of pre-split total)"
        )
    print(
        f"Records coded as Systematic Review: {systematic_review_count} "
        f"({systematic_review_pct:.2f}% of pre-split total)\n"
    )


if __name__ == "__main__":

    script_dir = os.path.dirname(os.path.abspath(__file__))
    study_design_to_level_path = os.path.join(script_dir, "01_study_design_to_loe_HETP.json")

    if len(sys.argv) != 2:
        print_error_msg(
            "Usage: python 01_automated_coding_loe.py <path_to_eppi_export.json>"
        )
        sys.exit(1)

    wp_path = sys.argv[1]

    if valid_json_path(wp_path) and valid_json_path(study_design_to_level_path):
        main(wp_path, study_design_to_level_path)