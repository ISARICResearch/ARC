from __future__ import annotations


__all__ = [
    "ArcApiClient",
    "ArcApiClientError",
]


# -- IMPORTS --

# -- Standard libraries --
from os import getenv
from time import monotonic

# -- External libraries --
import pandas as pd
import requests
from requests.exceptions import RequestException

# -- Internal libraries --
from arc.utils import CONSTANTS, setup_logger


logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True

_VERSION_SHA_CACHE: dict[tuple[str, str], str] = {}
_ARC_DF_CACHE: dict[tuple[str, str, str], pd.DataFrame] = {}
_ARC_TRANSLATION_DF_CACHE: dict[tuple[str, str, str], pd.DataFrame] = {}
_ARC_LIST_DF_CACHE: dict[tuple[str, str, str, str], pd.DataFrame] = {}
_ARC_VERSION_LIST_CACHE: dict[tuple[str], tuple[list, float]] = {}
_ARC_LANGUAGE_LIST_CACHE: dict[tuple[str, str], list] = {}

# Version/language metadata can change over time, so cache with TTL.
# Default 6 hours; override with ARC_METADATA_CACHE_TTL_SECONDS env var.
ARC_METADATA_CACHE_TTL_SECONDS = int(getenv("ARC_METADATA_CACHE_TTL_SECONDS", "21600"))


class ArcApiClientError(Exception):
    """Base ARC API client exception class."""

    pass


class ArcApiClient:
    """ARC API client.

    The default client environment is ``"production"``. The development
    environment (``"development"``) is meant for local development and testing.

    Examples
    --------
    >>> from arc.arc_api import ArcApiClient
    >>> client = ArcApiClient()
    >>> client
    arc.arc_api.ArcApiClient(environment="production")
    """

    def __init__(self) -> None:
        if getenv("ENV") == "development":
            self._environment = "development"
        else:
            self._environment = "production"

        self._base_url_api: str = CONSTANTS.API_BASE_URL.value
        self._base_url_raw_content: str = CONSTANTS.API_BASE_URL_RAW.value
        cls = type(self)
        self._repr_str = (
            f'{cls.__module__}.{cls.__qualname__}(environment="{self.environment}")'
        )

    def __repr__(self) -> str:
        return self._repr_str

    @property
    def environment(self) -> str:
        """:py:class:`str` : The client environment."""
        return self._environment

    @property
    def base_url_api(self) -> str:
        """:py:class:`str` : The API base URL."""
        return self._base_url_api

    @property
    def base_url_raw_content(self) -> str:
        """:py:class:`str` : The API base URL for raw file content."""
        return self._base_url_raw_content

    @staticmethod
    def _get_api_response(data_url: str) -> dict:
        logger.debug(
            "GITHUB_TOKEN is set"
            if getenv("GITHUB_TOKEN")
            else "GITHUB_TOKEN is not set. Making unauthenticated request"
        )

        # Use GITHUB_TOKEN if it exists; otherwise, make unauthenticated request
        # Unauthenticated requests are limited to 60 requests per hour
        github_token = getenv("GITHUB_TOKEN")
        headers = {"Authorization": f"token {github_token}"} if github_token else {}

        try:
            if github_token:
                logger.debug("Making authenticated request to GitHub API")
            response = requests.get(data_url, headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to fetch data: '{data_url}'")
        response_json = response.json()

        return response_json

    @staticmethod
    def _write_to_dataframe(data_path: str, json: bool = False) -> pd.DataFrame:
        try:
            if json:
                df = pd.read_json(data_path, encoding="utf-8")
            else:
                df = pd.read_csv(data_path, encoding="utf-8")
        except UnicodeDecodeError:
            if json:
                df = pd.read_json(data_path, encoding="latin1")
            else:
                df = pd.read_csv(data_path, encoding="latin1")
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to read data: {data_path}")

        return df

    def get_arc_version_list(self) -> list[str]:
        """:py:class:`list` : A list of ARC release version strings, sorted in descending order from the most recent release.

        .. note::

           ARC release versions are almost always linked to changes in the ARC
           schema. They are **NOT** the same as the ARC Python package
           versions.

        Returns
        -------
        list
            A list of ARC release version strings, sorted in descending order
            from the most recent release.

        Examples
        --------
        >>> import os; os.environ.update({"ENV": "production"})
        >>> from arc.arc_api import ArcApiClient
        >>> ArcApiClient().get_arc_version_list() # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        ['v1.6.1',
         'v1.6.0',
         'v1.5.0',
         'v1.4.1',
         'v1.4.0',
         'v1.3.0',
         'v1.2.2',
         'v1.2.1',
         'v1.2.0',
         'v1.1.5',
         'v1.1.4',
         'v1.1.3',
         'v1.1.2',
         'v1.1.1',
         'v1.1.0',
         'v1.0.4',
         'v1.0.3',
         'v1.0.2',
         'v1.0.1',
         'v1.0.0']
        """
        cache_key = (self.environment,)
        cache_entry = _ARC_VERSION_LIST_CACHE.get(cache_key)
        if cache_entry is not None:
            cached_list, cached_at = cache_entry
            if monotonic() - cached_at < ARC_METADATA_CACHE_TTL_SECONDS:
                return list(cached_list)

        if self.environment != "development":
            url = "/".join([self.base_url_api, "ARC", "releases"])
            release_json = self._get_api_response(url)
            version_list = [release_dict["tag_name"] for release_dict in release_json]
        else:
            url = "/".join([self.base_url_api, "DataPlatform", "contents", "ARCH"])
            release_json = self._get_api_response(url)
            version_list = sorted(
                [
                    self.get_version_string(release_dict["name"])
                    for release_dict in release_json
                    if release_dict["name"].startswith("ARCH")
                ],
                reverse=True,
            )
        _ARC_VERSION_LIST_CACHE[cache_key] = (list(version_list), monotonic())

        return version_list

    def get_arc_version_sha(self, version: str) -> str:
        """:py:class:`str` : The full commit SHA of the given ARC release version.

        .. note::

           ARC release versions are almost always linked to changes in the ARC
           schema. They are **NOT** the same as the ARC Python package
           versions.

        Parameters
        ----------
        version : str
            An ARC release version string.

        Returns
        -------
        str
            The full commit SHA of the given ARC release version.

        Examples
        --------
        >>> import os; os.environ.update({"ENV": "production"})
        >>> from arc.arc_api import ArcApiClient
        >>> ArcApiClient().get_arc_version_sha('v1.6.1') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        '8b6ccdd5cad0775b8b695a77f45a5cad41dabeed'
        """
        cache_key = (self.environment, version)
        if cache_key in _VERSION_SHA_CACHE:
            return _VERSION_SHA_CACHE[cache_key]

        try:
            if self.environment != "development":
                url = "/".join([self.base_url_api, "ARC", "tags"])
                tag_json = self._get_api_response(url)
                version_dict = list(filter(lambda x: x["name"] == version, tag_json))[0]
                version_sha = version_dict["commit"]["sha"]
            else:
                # Get the latest commit as the code is not tagged
                url = "/".join([self.base_url_api, "DataPlatform", "commits"])
                tag_json = self._get_api_response(url)
                version_dict = tag_json[0]
                version_sha = version_dict["sha"]
            _VERSION_SHA_CACHE[cache_key] = version_sha
            return version_sha
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(
                f"Unable to determine commit for version '{version}'"
            )

    def get_dataframe_arc_sha(
        self, sha: str, version: str | None = None
    ) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : The raw ARC schema for a given release version, as a Pandas dataframe.

        Parameters
        ----------
        sha : str
            Partial or full ARC commit SHA, usually one that is associated
            with a release version. The SHA string should be at least the
            first 8 characters of the full commit SHA.

        version : str, default=None
            Optional ARC release version for development mode, defaults to
            ``None``.

        Returns
        -------
        pandas.DataFrame
            The raw ARC schema for the given commit SHA.

        Examples
        --------
        >>> import os; os.environ.update({"ENV": "production"})
        >>> from arc.arc_api import ArcApiClient
        >>> data = ArcApiClient().get_dataframe_arc_sha('8b6ccdd5') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        >>> assert not data.empty
        """
        cache_key = (self.environment, sha, version)
        if cache_key in _ARC_DF_CACHE:
            return _ARC_DF_CACHE[cache_key].copy(deep=True)

        if self.environment != "development":
            url = "/".join([self.base_url_raw_content, "ARC", sha, "ARC.csv"])
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    sha,
                    "ARCH",
                    self.get_arch_version_string(version),
                    "ARCH.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        _ARC_DF_CACHE[cache_key] = df.copy(deep=True)

        return df.copy(deep=True)

    def get_dataframe_arc_version_language(
        self, version: str, language: str
    ) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : The translated ARC schema for a given release version and language, as a Pandas dataframe.

        Parameters
        ----------
        version : str
            ARC release version.

        language : str
            The target translation language.

        Returns
        -------
        pandas.DataFrame
            The translated ARC schema for the given release version and target
            language.

        Examples
        --------
        >>> import os; os.environ.update({"ENV": "production"})
        >>> from arc.arc_api import ArcApiClient
        >>> data = ArcApiClient().get_dataframe_arc_version_language('v1.6.1', 'French') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        >>> assert not data.empty
        """
        cache_key = (self.environment, version, language)
        if cache_key in _ARC_TRANSLATION_DF_CACHE:
            return _ARC_TRANSLATION_DF_CACHE[cache_key].copy(deep=True)

        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "ARCH.csv",
                ]
            )
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    "main",
                    "ARCH",
                    self.get_arch_version_string(version),
                    "ARCH.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        _ARC_TRANSLATION_DF_CACHE[cache_key] = df.copy(deep=True)

        return df.copy(deep=True)

    def get_dataframe_arc_list_version_language(
        self, version: str, language: str, list_name: str
    ) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : A translated ARC schema options list for a given release version and target language, as a Pandas dataframe.

        Parameters
        ----------
        version : str
            ARC release version.

        language : str
            The target translation language.

        list_name : str
            The list name as a path string excluding the file suffix, e.g.
            ::

                conditions/Comorbidities
                demographics/Country
                drugs/Antibiotics

            etc.

        Returns
        -------
        pandas.DataFrame
            The translated ARC schema options list for a given release version
            and target language, as a Pandas dataframe.

        Examples
        --------
        >>> from arc.arc_api import ArcApiClient
        >>> data = ArcApiClient().get_dataframe_arc_list_version_language('v1.6.1', 'Spanish', 'drugs/Antibiotics') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        >>> assert not data.empty
        """
        cache_key = (self.environment, version, language, list_name)
        if cache_key in _ARC_LIST_DF_CACHE:
            return _ARC_LIST_DF_CACHE[cache_key].copy(deep=True)

        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "Lists",
                    f"{list_name}.csv",
                ]
            )
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    "main",
                    "ARCH",
                    self.get_arch_version_string(version),
                    "Lists",
                    f"{list_name}.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        df = df.sort_values(by=df.columns[0], ascending=True).reset_index(drop=True)
        _ARC_LIST_DF_CACHE[cache_key] = df.copy(deep=True)

        return df.copy(deep=True)

    def get_arc_language_list_version(self, version: str | None) -> list[str]:
        """:py:class:`list` : A list of supported languages in which translations are available, for a given release version.

        Parameters
        ----------
        version : str
            ARC release version.

        Returns
        -------
        list
            A list of supported languages in which translations are available
            for the given release.

        Examples
        --------
        >>> from arc.arc_api import ArcApiClient
        >>> ArcApiClient().get_arc_language_list_version('v1.6.1') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        ['English', 'French', 'Portuguese', 'Spanish']
        """
        normalized_version = str(version)
        cache_key = (self.environment, normalized_version)
        cache_entry = _ARC_LANGUAGE_LIST_CACHE.get(cache_key)
        if cache_entry is not None:
            return list(cache_entry)

        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_api,
                    "ARC-Translations",
                    "contents",
                    self.get_arch_version_string(version),
                ]
            )
            language_json = self._get_api_response(url)
            df = pd.DataFrame.from_dict(language_json)
            language_list = df["name"].to_list()
        else:
            language_list = ["English"]
        _ARC_LANGUAGE_LIST_CACHE[cache_key] = list(language_list)

        return language_list

    def get_dataframe_paper_like_details(
        self, version: str, language: str
    ) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : The paperlike CRF completion guide, for a given release version and target language, as a Pandas dataframe.

        Parameters
        ----------
        version : str
            ARC release version.

        language : str
            The target translation language.

        Returns
        -------
        pandas.DataFrame
            The paperlike CRF completion guide, for a given release version and
            target language.

        Examples
        --------
        >>> from arc.arc_api import ArcApiClient
        >>> ArcApiClient().get_dataframe_paper_like_details('v1.6.1', 'French') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
                               Paper-like section  ...                                   Text_translation
        0                                   Title  ...                                 CRF DE BASE ISARIC
        1   DESIGN OF THIS CASE REPORT FORM (CRF)  ...  Ce CRF est configuré en modules à utiliser pou...
        2                       PRESENTATION FORM  ...  TOUJOURS compléter le premier jour de présenta...
        3                       PRESENTATION FORM  ...  Calendrier/Événements : Admission à l’hôpital ...
        4                              DAILY FORM  ...  TOUJOURS compléter le premier jour de présenta...
        5                              DAILY FORM  ...  SI APPLICABLE, à compléter le jour de l'admiss...
        6                              DAILY FORM  ...  OPTION à compléter les jours où des échantillo...
        7                              DAILY FORM  ...  OPTION à compléter quotidiennement si cela pré...
        8                              DAILY FORM  ...  Calendrier/Événements : Admission à l'hôpital ...
        9                            OUTCOME FORM  ...  TOUJOURS compléter à la sortie ou au décès ou ...
        10                           OUTCOME FORM  ...    Moment/Événements : Sortie/décès/fin des études
        11                         FOLLOW-UP FORM  ...  Calendrier/événements : selon le protocole du ...
        12                        WITHDRAWAL FORM  ...  Calendrier/événements : selon le protocole du ...
        13                      Follow-up details  ...  Continuer à suivre les patients qui sont trans...
        14                         PREGNANCY FORM  ...  OPTION à compléter pour une personne enceinte ...
        15                         PREGNANCY FORM  ...  Calendrier/Événements : Personnes enceintes – ...
        16                           NEONATE FORM  ...  OPTION à compléter pour les nouveau-nés OU si ...
        17                           NEONATE FORM  ...  Calendrier/Événements : Nouveau-né – lors de l...
        18                         Timing /Events  ...  Admission à l'hôpital / évaluation initiale | ...
        19                       GENERAL GUIDANCE  ...  Contactez le centre de support mondial ISARIC ...
        20                       GENERAL GUIDANCE  ...  Le CRF est conçu pour collecter des données ob...
        21                       GENERAL GUIDANCE  ...  Veuillez vous référer aux lignes directrices p...
        22                       GENERAL GUIDANCE  ...  Votre établissement peut capturer des données ...
        23                       GENERAL GUIDANCE  ...  Les numéros d'identification des participants ...
        24                       GENERAL GUIDANCE  ...  Pour les participants qui reviennent pour une ...
        25                       GENERAL GUIDANCE  ...  Pour les participants qui effectuent un transf...
        26                       GENERAL GUIDANCE  ...  Les sélections avec des cercles () sont des sé...
        """
        try:
            if self.environment != "development":
                url = "/".join(
                    [
                        self.base_url_raw_content,
                        "ARC-Translations",
                        "main",
                        self.get_arch_version_string(version),
                        language,
                        "paper_like_details.csv",
                    ]
                )
            else:
                url = "/".join(
                    [
                        self.base_url_raw_content,
                        "DataPlatform",
                        "main",
                        "ARCH",
                        self.get_arch_version_string(version),
                        "paper_like_details.csv",
                    ]
                )
            df = self._write_to_dataframe(url)
        except ArcApiClientError as e:
            raise ArcApiClientError(
                "Could not find paperlike details CSV for ARC version "
                f'"{version}" and language "{language}"'
            ) from e
        else:
            return df

    def get_dataframe_supplemental_phrases(
        self, version: str, language: str
    ) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : The supplemental phrases CSV for a given release version and target language, as a Pandas dataframe.

        Parameters
        ----------
        version : str
            ARC release version.

        language : str
            The target translation language.

        Returns
        -------
        pandas.DataFrame
            The supplemental phrases CSV, for a given release version and
            target language.

        Examples
        --------
        >>> from arc.arc_api import ArcApiClient
        >>> ArcApiClient().get_dataframe_supplemental_phrases('v1.6.1', 'English') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
                           variable                                               text
        0                    select                                             Select
        1                   specify                                            Specify
        2             specify_other                                      Specify other
        3   specify_other_infection  Specify other infection the individual is susp...
        4               other_agent  other agents administered while hospitalised o...
        5         select_additional                                  Select additional
        6            any_additional                                     Any additional
        7                     other                                              Other
        8                     units                                              Units
        9                        if                                                 If
        10          if_completeForm                          If Yes, complete the form
        """
        try:
            if self.environment != "development":
                url = "/".join(
                    [
                        self.base_url_raw_content,
                        "ARC-Translations",
                        "main",
                        self.get_arch_version_string(version),
                        language,
                        "supplemental_phrases.csv",
                    ]
                )
            else:
                # Use the latest ARC one
                url = "/".join([self.base_url_api, "ARC", "releases"])
                release_json = self._get_api_response(url)
                version_list = [
                    release_dict["tag_name"] for release_dict in release_json
                ]
                url = "/".join(
                    [
                        self.base_url_raw_content,
                        "ARC-Translations",
                        "main",
                        self.get_arch_version_string(max(version_list)),
                        language,
                        "supplemental_phrases.csv",
                    ]
                )
            df = self._write_to_dataframe(url)
        except ArcApiClientError as e:
            raise ArcApiClientError(
                "Could not find paperlike details CSV for ARC version "
                f'"{version}" and language "{language}"'
            ) from e
        else:
            return df

    def get_dataframe_crf_metadata(self, version: str) -> pd.DataFrame:
        """:py:class:`pandas.DataFrame` : The CRF metadata CSV, in English, as a Pandas dataframe.

        Only an English language version is available.

        Parameters
        ----------
        version : str
            ARC version string.

        Returns
        -------
        pandas.DataFrame
            The CRF metadata.

        Raises
        ------
        bridge.arc.arc_api.ArcApiClientError
            In case of a non-matching ARC version or a request error.

        Examples
        --------
        >>> from arc.arc_api import ArcApiClient
        >>> data = ArcApiClient().get_dataframe_crf_metadata('v1.6.1') # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        >>> assert not data.empty
        """
        try:
            # Try to fetch the CSV from the given release refs:
            #
            #   https://raw.githubusercontent.com/ISARICResearch/ARC/refs/tags/<version>/crf_metadata.csv
            #
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC",
                    "refs",
                    "tags",
                    version,
                    "crf_metadata.csv",
                ]
            )
            df = self._write_to_dataframe(url)
        except ArcApiClientError as e:
            raise ArcApiClientError(
                "Could not find CRF metadata CSV for ARC version "
                f'"{version}" and English language'
            ) from e
        else:
            return df

    @staticmethod
    def get_arch_version_string(version: str) -> str:
        return f'ARCH{str(version.replace('v', ''))}'

    @staticmethod
    def get_version_string(version: str) -> str:
        return f'v{str(version.replace('ARCH', ''))}'


if __name__ == "__main__":  # pragma: no cover
    # Doctest the module from the project root using
    #
    #     PYTHONPATH="src" python3 -m doctest -v arc/arc_api.py  # noqa : E501
    #
    import doctest

    doctest.testmod()
