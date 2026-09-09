from __future__ import annotations


__all__ = [
    "ArcList",
]


# -- IMPORTS --

# -- Standard libraries --
from typing import List, Tuple

# -- 3rd party libraries --
import pandas as pd

# -- Internal libraries --
from arc import arc_translations
from arc.arc_api import ArcApiClient
from arc.utils import setup_logger


logger = setup_logger(__name__)

ARROWS = ["", ">", "->", ">->", "->->", ">->->"]


class ArcList:
    def __init__(self, version: str, language: str):
        self.version = version
        self.language = language
        self._list_df_cache: dict[str, pd.DataFrame] = {}

    def _get_list_options_df(self, list_name: str) -> pd.DataFrame:
        normalized_list_name = str(list_name).replace("_", "/")
        if normalized_list_name not in self._list_df_cache:
            self._list_df_cache[normalized_list_name] = (
                ArcApiClient().get_dataframe_arc_list_version_language(
                    self.version,
                    self.language,
                    normalized_list_name,
                )
            )
        return self._list_df_cache[normalized_list_name].copy(deep=True)

    def _get_list_choices(
        self, datadicc_row: pd.Series, other_text: str
    ) -> Tuple[str, list]:
        df_list_options = self._get_list_options_df(str(datadicc_row["List"]))

        list_choices = ""
        list_variable_choices_aux = []

        for list_option in df_list_options[df_list_options.columns[0]]:
            cont_lo = self._get_list_option_number(df_list_options, str(list_option))
            try:
                list_variable_choices_aux.append([cont_lo, list_option])
                list_choices += f"{str(cont_lo)}, {str(list_option)} | "
            except Exception as e:
                logger.error(e)
                raise RuntimeError("Failed to determine list choices")

        list_choices = f"{list_choices}88, {other_text}"

        return (
            list_choices,
            list_variable_choices_aux,
        )

    @staticmethod
    def _get_question_upper_lower(
        datadicc_row: pd.Series, question_english_lower: str
    ) -> str:
        if question_english_lower == "nsaids":
            question = datadicc_row["Question"]
        else:
            question = datadicc_row["Question"].lower()
        return question

    def _get_question_text_dropdown_row_list_content(
        self,
        datadicc_row: pd.Series,
        iteration_number: int,
        select_text: str,
        select_additional_text: str,
    ) -> str:
        question_english_lower = str(datadicc_row["Question_english"].lower())
        question = self._get_question_upper_lower(datadicc_row, question_english_lower)

        if iteration_number == 0:
            if "select" in question_english_lower:
                question_text = f"{ARROWS[iteration_number]}{question}"
            else:
                question_text = f"{ARROWS[iteration_number]} {select_text} {question}"

        else:
            question_suffix = str(iteration_number + 1)
            if "select" in question_english_lower:
                question_text = (
                    f"{ARROWS[iteration_number]}{question} {question_suffix}"
                )
            else:
                question_text = f"{ARROWS[iteration_number]} {select_additional_text} {question} {question_suffix}"

        return question_text

    def _format_dropdown_row_list_content(
        self,
        datadicc_row: pd.Series,
        iteration_number: int,
        list_choices: str,
        select_text: str,
        select_additional_text: str,
    ) -> pd.Series:
        dropdown_row = datadicc_row.copy()
        dropdown_row["Variable"] = (
            f'{datadicc_row['Sec']}_{datadicc_row['vari']}_{str(iteration_number)}item'
        )
        dropdown_row["Answer Options"] = list_choices
        dropdown_row["Type"] = "dropdown"
        dropdown_row["Validation"] = "autocomplete"
        dropdown_row["Maximum"] = None
        dropdown_row["Minimum"] = None
        dropdown_row["List"] = None
        question_text = self._get_question_text_dropdown_row_list_content(
            datadicc_row,
            iteration_number,
            select_text,
            select_additional_text,
        )
        dropdown_row["Question"] = question_text
        dropdown_row["mod"] = f"{str(iteration_number)}item"
        dropdown_row["vari"] = datadicc_row["vari"]
        if iteration_number == 0:
            dropdown_row["Skip Logic"] = f"[{datadicc_row['Variable']}]='1'"
        else:
            dropdown_row["Skip Logic"] = (
                f"[{datadicc_row['Sec']}_{datadicc_row['vari']}_{str(iteration_number - 1)}addi]='1'"
            )
        return dropdown_row

    def _get_question_text_other_row_list_content(
        self,
        datadicc_row: pd.Series,
        iteration_number: int,
        specify_text: str,
        specify_other_text: str,
        specify_other_infection_text: str,
    ) -> str:
        if datadicc_row["Variable"] == "inclu_disease":
            question_text = f"{ARROWS[iteration_number]} {specify_other_infection_text}"

        else:
            question_english_lower = str(datadicc_row["Question_english"].lower())
            question = self._get_question_upper_lower(
                datadicc_row, question_english_lower
            )

            if iteration_number == 0:
                if "other" in question_english_lower:
                    question_text = (
                        f"{ARROWS[iteration_number]} {specify_text} {question}"
                    )
                else:
                    question_text = (
                        f"{ARROWS[iteration_number]} {specify_other_text} {question}"
                    )

            else:
                question_suffix = str(iteration_number + 1)
                if "other" in question_english_lower:
                    question_text = f"{ARROWS[iteration_number]} {specify_text} {question} {question_suffix}"
                else:
                    question_text = f"{ARROWS[iteration_number]} {specify_other_text} {question} {question_suffix}"

        return question_text

    def _format_other_row_list_content(
        self,
        datadicc_row: pd.Series,
        iteration_number: int,
        dropdown_row: pd.Series,
        specify_text: str,
        specify_other_text: str,
        specify_other_infection_text: str,
    ) -> pd.Series:
        other_row = datadicc_row.copy()
        other_row["Variable"] = (
            f'{datadicc_row['Variable']}_{str(iteration_number)}otherl2'
        )
        other_row["Answer Options"] = None
        other_row["Type"] = "text"
        other_row["Maximum"] = None
        other_row["Minimum"] = None
        other_row["Skip Logic"] = f"[{dropdown_row['Variable']}]='88'"
        question_text = self._get_question_text_other_row_list_content(
            datadicc_row,
            iteration_number,
            specify_text,
            specify_other_text,
            specify_other_infection_text,
        )
        other_row["Question"] = question_text
        other_row["List"] = None
        other_row["mod"] = f"{str(iteration_number)}otherl2"
        other_row["vari"] = datadicc_row["vari"]
        return other_row

    @staticmethod
    def _append_updated_other_info_list_content(
        datadicc_row: pd.Series,
        iteration_number: int,
        df_other_info: pd.DataFrame,
        questions_for_this_list: list,
    ) -> List:
        skip_logic_variable = f'{datadicc_row['Sec']}_{datadicc_row['vari']}_{str(iteration_number)}addi'.replace(
            str(iteration_number), str(iteration_number - 1)
        )

        if len(df_other_info) > 1:
            for index, other_info_row in df_other_info.iterrows():
                other_info_row_updated = other_info_row.copy()
                if iteration_number == 0:
                    question_text = (
                        f'{ARROWS[iteration_number]} {datadicc_row['Question']}'
                    )
                else:
                    question_text = f'{ARROWS[iteration_number]} {datadicc_row['Question']} {str(iteration_number + 1)}'
                other_info_row_updated["Question"] = question_text
                other_info_row_updated["Variable"] = (
                    f'{datadicc_row['Sec']} {datadicc_row['vari']}_{str(iteration_number)}{datadicc_row['mod']}'
                )
                other_info_row_updated["Skip Logic"] = f"[{skip_logic_variable}]='1'"
                other_info_row_updated["List"] = None
                other_info_row_updated["mod"] = (
                    f'{str(iteration_number)}{datadicc_row['mod']}'
                )
                other_info_row_updated["vari"] = datadicc_row["vari"]
                questions_for_this_list.append(other_info_row_updated)

        elif len(df_other_info) == 1:
            other_info_row = df_other_info.iloc[0]
            other_info_row_updated = other_info_row.copy()
            if iteration_number == 0:
                other_info_row_updated["Question"] = (
                    f'{ARROWS[iteration_number]}{other_info_row['Question']}'
                )
            else:
                question_text = f'{ARROWS[iteration_number]}{other_info_row['Question']} {str(iteration_number + 1)}'
                other_info_row_updated["Question"] = question_text
                other_info_row_updated["Skip Logic"] = f"[{skip_logic_variable}]='1'"
                other_info_row_updated["Variable"] = (
                    f'{other_info_row['Sec']}_{other_info_row['vari']}_{str(iteration_number)}{other_info_row['mod']}'
                )
                other_info_row_updated["List"] = None
                other_info_row_updated["mod"] = (
                    f'{str(iteration_number)}{other_info_row['mod']}'
                )
                other_info_row_updated["vari"] = other_info_row["vari"]
            questions_for_this_list.append(other_info_row_updated)

        return questions_for_this_list

    def _append_updated_additional_row_list_content(
        self,
        datadicc_row: pd.Series,
        iteration_number: int,
        iteration_total: int,
        dropdown_row: pd.Series,
        any_additional_text: str,
        questions_for_this_list: list,
    ) -> List:
        if iteration_number < iteration_total - 1:
            additional_row = datadicc_row.copy()
            additional_row["Variable"] = (
                f'{datadicc_row['Sec']}_{datadicc_row['vari']}_{str(iteration_number)}addi'
            )
            additional_row["Answer Options"] = datadicc_row["Answer Options"]
            additional_row["Type"] = "radio"
            additional_row["Maximum"] = None
            additional_row["Minimum"] = None
            additional_row["Skip Logic"] = dropdown_row["Skip Logic"]
            question_english_lower = str(datadicc_row["Question_english"].lower())
            question = self._get_question_upper_lower(
                datadicc_row, question_english_lower
            )
            question_text = (
                f"{ARROWS[iteration_number]} {any_additional_text} {question} ?"
            )
            additional_row["Question"] = question_text
            additional_row["List"] = None
            additional_row["mod"] = f"{str(iteration_number)}addi"
            additional_row["vari"] = datadicc_row["vari"]
            questions_for_this_list.append(additional_row)
        return questions_for_this_list

    def get_list_content(self, df_datadicc: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        all_rows_lists = []
        list_variable_choices = []
        df_datadicc_lists = df_datadicc.loc[df_datadicc["Type"] == "list"]

        translations_for_language = arc_translations.get_translations(self.language)
        select_text = translations_for_language["select"]
        specify_text = translations_for_language["specify"]
        specify_other_text = translations_for_language["specify_other"]
        specify_other_infection_text = translations_for_language[
            "specify_other_infection"
        ]
        select_additional_text = translations_for_language["select_additional"]
        any_additional_text = translations_for_language["any_additional"]
        other_text = translations_for_language["other"]

        for _, datadicc_row in df_datadicc_lists.iterrows():
            if pd.isnull(datadicc_row["List"]):
                logger.warning("List without corresponding repository file")

            else:
                (list_choices, list_variable_choices_aux) = self._get_list_choices(
                    datadicc_row, other_text
                )

                iteration_total = 5
                questions_for_this_list = []

                for iteration_number in range(iteration_total):
                    dropdown_row = self._format_dropdown_row_list_content(
                        datadicc_row,
                        iteration_number,
                        list_choices,
                        select_text,
                        select_additional_text,
                    )

                    other_row = self._format_other_row_list_content(
                        datadicc_row,
                        iteration_number,
                        dropdown_row,
                        specify_text,
                        specify_other_text,
                        specify_other_infection_text,
                    )

                    questions_for_this_list.append(dropdown_row)
                    questions_for_this_list.append(other_row)

                    other_info = df_datadicc.loc[
                        (df_datadicc["Sec"] == datadicc_row["Sec"])
                        & (df_datadicc["vari"] == datadicc_row["vari"])
                        & (df_datadicc["Variable"] != datadicc_row["Variable"])
                    ]

                    questions_for_this_list = (
                        self._append_updated_other_info_list_content(
                            datadicc_row,
                            iteration_number,
                            other_info,
                            questions_for_this_list,
                        )
                    )

                    questions_for_this_list = (
                        self._append_updated_additional_row_list_content(
                            datadicc_row,
                            iteration_number,
                            iteration_total,
                            dropdown_row,
                            any_additional_text,
                            questions_for_this_list,
                        )
                    )

                all_rows_lists.append(datadicc_row)

                for question_for_this_list in questions_for_this_list:
                    all_rows_lists.append(question_for_this_list)

                list_variable_choices.append(
                    [datadicc_row["Variable"], list_variable_choices_aux]
                )

        df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)

        return df_arc_list, list_variable_choices

    @staticmethod
    def _get_list_option_number(df_list_options: pd.DataFrame, list_option: str) -> int:
        if "Value" in df_list_options.columns:
            list_option_number = int(
                df_list_options["Value"]
                .loc[df_list_options[df_list_options.columns[0]] == list_option]
                .iloc[0]
            )
        else:
            # fallback to index-based counting
            list_option_number = (
                df_list_options[df_list_options.columns[0]]
                .values.tolist()
                .index(list_option)
                + 1
            )

        if list_option_number == 88:
            list_option_number = 89
        elif list_option_number == 99:
            list_option_number = 100
        return list_option_number

    @staticmethod
    def _get_list_data_dropdown_other_rows(
        row: pd.Series, translations_for_language: dict, list_type: str, l2_choices: str
    ) -> Tuple[pd.Series, pd.Series]:
        select_text = translations_for_language["select"]
        specify_text = translations_for_language["specify"]
        specify_other_text = translations_for_language["specify_other"]
        other_agent_text = translations_for_language["other_agent"]

        dropdown_row = row.copy()
        other_row = row.copy()
        dropdown_row["Variable"] = f'{row['Variable']}_otherl2'
        dropdown_row["Answer Options"] = l2_choices
        dropdown_row["Type"] = "dropdown"
        dropdown_row["Validation"] = "autocomplete"
        dropdown_row["Maximum"] = None
        dropdown_row["Minimum"] = None
        dropdown_row["List"] = None

        if row["Variable"] == "medi_medtype":
            dropdown_row["Question"] = f"{select_text} {other_agent_text}"
            other_row["Question"] = f"{specify_text} {other_agent_text}"
        else:
            question = row["Question"]
            dropdown_row["Question"] = f"{select_text} {question}"
            other_row["Question"] = f"{specify_other_text} {question}"

        dropdown_row["mod"] = "otherl2"

        if list_type == "multi_list":
            dropdown_row["Skip Logic"] = f"[{row['Variable']}(88)]='1'"
        else:
            dropdown_row["Skip Logic"] = f"[{row['Variable']}]='88'"

        other_row["Variable"] = f'{row['Variable']}_otherl3'
        other_row["Answer Options"] = None
        other_row["Type"] = "text"
        other_row["Maximum"] = None
        other_row["Minimum"] = None

        if row["Variable"] != "inclu_disease":
            other_row["Skip Logic"] = f"[{row['Variable']}_otherl2]='88'"
        else:
            other_row["Skip Logic"] = f"[{row['Variable']}]='88'"

        other_row["List"] = None
        other_row["mod"] = "otherl3"

        return dropdown_row, other_row

    def _get_list_data(
        self, df_datadicc: pd.DataFrame, list_type: str
    ) -> tuple[list, list]:
        all_rows_lists = []
        list_variable_choices = []
        datadicc_disease_lists = df_datadicc.loc[df_datadicc["Type"] == list_type]
        translations_for_language = arc_translations.get_translations(self.language)
        other_text = translations_for_language["other"]

        for _, row in datadicc_disease_lists.iterrows():
            if pd.isnull(row["List"]):
                logger.warning("List without corresponding repository file")
            else:
                df_list_options = self._get_list_options_df(str(row["List"]))

                l2_choices = ""
                l1_choices = ""
                list_variable_choices_aux = []
                for list_option in df_list_options[df_list_options.columns[0]]:
                    list_option_number = self._get_list_option_number(
                        df_list_options, str(list_option)
                    )
                    try:
                        df_list_options["Selected"] = pd.to_numeric(
                            df_list_options["Selected"], errors="coerce"
                        )

                        selected_value = (
                            df_list_options["Selected"]
                            .loc[
                                df_list_options[df_list_options.columns[0]]
                                == list_option
                            ]
                            .iloc[0]
                        )

                        choices_text = (
                            f"{str(list_option_number)}, {str(list_option)} | "
                        )
                        if selected_value == 1:
                            l1_choices += choices_text
                            list_variable_choices_aux.append(
                                [list_option_number, list_option, 1]
                            )
                        else:
                            l2_choices += choices_text
                            list_variable_choices_aux.append(
                                [list_option_number, list_option, 0]
                            )

                    except Exception as e:
                        logger.error(e)
                        raise RuntimeError("Failed to add to lists of choices")

                list_variable_choices.append(
                    [row["Variable"], list_variable_choices_aux]
                )

                row["Answer Options"] = f"{l1_choices}88, {other_text}"

                l2_choices = f"{l2_choices}88, {other_text}"
                (dropdown_row, other_row) = self._get_list_data_dropdown_other_rows(
                    row, translations_for_language, list_type, l2_choices
                )

                all_rows_lists.append(row)
                if row["Variable"] != "inclu_disease":
                    all_rows_lists.append(dropdown_row)
                all_rows_lists.append(other_row)

        return list_variable_choices, all_rows_lists

    def get_user_list_content(
        self, df_datadicc: pd.DataFrame
    ) -> tuple[pd.DataFrame, list]:
        ulist_variable_choices, all_rows_lists = self._get_list_data(
            df_datadicc, "user_list"
        )
        df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)
        return df_arc_list, ulist_variable_choices

    def get_multi_list_content(
        self, df_datadicc: pd.DataFrame
    ) -> tuple[pd.DataFrame, list]:
        multilist_variable_choices, all_rows_lists = self._get_list_data(
            df_datadicc, "multi_list"
        )
        df_arc_list = pd.DataFrame(all_rows_lists).reset_index(drop=True)
        return df_arc_list, multilist_variable_choices
