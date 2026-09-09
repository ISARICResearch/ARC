from __future__ import annotations


__all__ = [
    "get_arc_translation",
    "get_translations",
    "process_skip_logic",
]


# -- IMPORTS --

# -- Standard libraries --
import re
from typing import Tuple

# -- 3rd party libraries --
import pandas as pd

# -- Internal libraries --
from arc.arc_api import ArcApiClient


def get_arc_translation(
    language: str, version: str, df_current_datadicc: pd.DataFrame
) -> pd.DataFrame:
    df_datadicc_english = ArcApiClient().get_dataframe_arc_version_language(
        version, "English"
    )

    df_merged_english = df_current_datadicc[["Variable"]].merge(
        df_datadicc_english.set_index("Variable"), on="Variable", how="left"
    )

    df_current_datadicc["Question_english"] = df_current_datadicc["Variable"].map(
        df_merged_english.set_index("Variable")["Question"]
    )

    df_current_datadicc["Question_english"] = df_current_datadicc[
        "Question_english"
    ].astype(str)

    df_datadicc_translated = ArcApiClient().get_dataframe_arc_version_language(
        version, language
    )

    df_merged = df_current_datadicc[["Variable"]].merge(
        df_datadicc_translated.set_index("Variable"), on="Variable", how="left"
    )
    columns_to_update = [
        "Form",
        "Section",
        "Question",
        "Answer Options",
        "Definition",
        "Completion Guideline",
    ]

    for col in columns_to_update:
        df_current_datadicc.loc[df_merged[col].notna(), col] = df_merged.loc[
            df_merged[col].notna(), col
        ]

    df_current_datadicc["Branch"] = df_current_datadicc.apply(
        lambda row: process_skip_logic(row, df_current_datadicc), axis=1
    )
    return df_current_datadicc


def _extract_logic_components(skip_logic_column: str) -> Tuple[list, list, list, list]:
    if isinstance(skip_logic_column, str) and pd.notna(skip_logic_column):
        normalized_logic = re.sub(
            r"\[([a-zA-Z0-9_]+)\((\d+)\)\]='(\d+)'", r"[\1]='\2'", skip_logic_column
        )

        variables = re.findall(r"\[([a-zA-Z0-9_]+)\]", normalized_logic)

        raw_values = re.findall(r"[=!<>]=?\s*('[^']*'|\d+\.?\d*)", normalized_logic)
        values = []
        for raw_value in raw_values:
            if raw_value.startswith("'") and raw_value.endswith("'"):
                values.append(raw_value.strip("'"))
            else:
                if "." in raw_value:
                    values.append(float(raw_value))
                else:
                    values.append(int(raw_value))

        comparison_operators = re.findall(r"(<=|>=|<>|[=><!]=?)", normalized_logic)

        logical_operators = re.findall(r"\b(and|or)\b", normalized_logic)

        return (
            variables,
            values,
            comparison_operators,
            logical_operators,
        )

    return (
        [],
        [],
        [],
        [],
    )


def process_skip_logic(row: pd.Series, df_current_datadicc: pd.DataFrame) -> str:
    branch = []
    if "Skip Logic" in df_current_datadicc.columns:
        skip_logic = row["Skip Logic"]
        extracted_variables, labels, comparison_operators, logical_operators = (
            _extract_logic_components(str(skip_logic))
        )
        logical_operators = logical_operators + [" "]
        for i in range(len(extracted_variables)):
            try:
                answers = (
                    df_current_datadicc["Answer Options"]
                    .loc[df_current_datadicc["Variable"] == extracted_variables[i]]
                    .iloc[0]
                )
                question = (
                    df_current_datadicc["Question"]
                    .loc[df_current_datadicc["Variable"] == extracted_variables[i]]
                    .iloc[0]
                )
                comp_operators = comparison_operators[i]
                if isinstance(answers, str) and pd.notna(answers):
                    pairs = answers.split(" | ")
                    dic_answer = {
                        pair.split(", ")[0]: pair.split(", ")[1] for pair in pairs
                    }
                    answers_label = dic_answer.get(labels[i], "Unknown")

                else:
                    answers_label = labels[i]
                branch.append(
                    f"({question} {comp_operators} {answers_label}) {logical_operators[i]}"
                )

            except IndexError:
                branch.append("Variable not found getARCTranslation")
            except Exception as e:
                branch.append(f"Error getARCTranslation: {str(e)}")

    return "  ".join(branch)


def get_translations(language: str | None) -> dict:
    translations = {
        "English": {
            "select": "Select",
            "specify": "Specify",
            "specify_other": "Specify other",
            "specify_other_infection": "Specify other infection the individual is suspected/confirmed to have",
            "other_agent": "other agents administered while hospitalised or at discharge",
            "select_additional": "Select additional",
            "any_additional": "Any additional",
            "other": "Other",
            "units": "Units",
        },
        "Spanish": {
            "select": "Seleccionar",
            "specify": "Especifique",
            "specify_other": "Especifique otro(a)",
            "specify_other_infection": "Especifique otra infección que se sospecha/ha confirmado en el individuo",
            "other_agent": "otros medicamentos administrados durante la hospitalización o al alta",
            "select_additional": "Seleccionar adicional",
            "any_additional": "Cualquier adicional",
            "other": "Otro(a)",
            "units": "Unidades",
        },
        "French": {
            "select": "Sélectionnez",
            "specify": "Précisez",
            "specify_other": "Précisez un(e) autre",
            "specify_other_infection": "Précisez une autre infection dont l’individu est suspecté/confirmé avoir",
            "other_agent": "autre(s) agent(s) administré(s) lors de l’hospitalisation ou à la sortie",
            "select_additional": "Sélectionner supplémentaire",
            "any_additional": "Tout supplémentaire",
            "other": "Autre",
            "units": "Unités",
        },
        "Portuguese": {
            "select": "Selecionar",
            "specify": "Especifique",
            "specify_other": "Especifique outro(a)",
            "specify_other_infection": "Especifique outra infecção que o indivíduo é suspeito/confirmado ter",
            "other_agent": "outros agentes administrados durante a hospitalização ou na alta",
            "select_additional": "Selecionar adicional",
            "any_additional": "Qualquer adicional",
            "other": "Outro(a)",
            "units": "Unidades",
        },
    }

    if language not in translations:
        raise ValueError(f"Language '{language}' is not supported.")

    return translations[language]
