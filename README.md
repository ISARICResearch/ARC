# ARC - Analysis and Research Compendium

ARC is a comprehensive machine-readable document in CSV format that contains a library of questions to be used in Clinical Report Forms (CRFs) during disease outbreaks. It covers a wide range of patient-related information, including demographics, comorbidities, signs and symptoms, medications, outcomes, and more. Each question in ARC has a variable name with specific guidelines and relevant parameters, such as coded answers, minimum and maximum limits, data types, skip logic, and more.

## About ARC

ARC (Analysis and Research Compendium) is designed to serve as a resource for researchers and healthcare professionals involved in the study of outbreaks and emerging public health threats. Here's what you need to know:

- **Machine-Readable**: ARC is provided in CSV format, making it easy for automated systems to read and process the data.

- **Version Control**: We maintain a comprehensive history of changes made to ARC using GitHub's version control. This ensures document integrity, traceability of changes, and seamless collaboration among researchers.

- **Open Access**: ARC is made openly available for the research community. While contributions are limited to authorized individuals, the document can be freely accessed and utilized by others.

## ARC Version 1.0.1
ARC Version 1.0.1 contains a library of questions to be used in Case Report Forms (CRFs) tailored for outbreak responses for COVID-19, Dengue, Mpox and H5Nx. The CRFs are grouped into five forms, ‘presentation’, ‘daily’, ‘medication’, ‘pathogen testing’, and ‘outcome’, which contain several sections including questions about inclusion and exclusion criteria, hospital admission, patient demographics, travel history, exposure history, pregnancy- and infant-related questions, comorbidities and risk factors, past medical history, medication (drug) history, vaccination history, vital signs assessment, signs and symptoms, clinical assessment, treatment and interventions, laboratory results, imaging results, pathogen testing as well as complications. The questions comprehensively capture the relevant information from the time of presentation to the health facility, daily assessment during admission and at the discharge from the health facility. 
- **COVID-19 Template:** The COVID-19 template of ARC Version 1.0.0 contains 319 questions to be used for CRFs for COVID-19 outbreak responses, grouped within the forms and sections described above. 
- **Dengue Template:** The Dengue template of ARC Version 1.0.0 contains 358 questions to be used for CRFs for Dengue outbreak responses, grouped within the forms and sections described above.
- **Mpox Preset:** The Mpox template of ARC Version 1.0.0 contains 413 questions to be used for CRFs for Mpox outbreak responses, grouped within the forms and sections described above. This preset has a section on skin and mucosal assessment for Mpox lesions. 
- **H5Nx Template:** The H5Nx template of ARC Version 1.0.0 contains 401 questions to be used for CRFs for Influenza H5Nx outbreak responses, grouped within the forms and sections described above.
- **Oropouche Questions:**
- Added user-generated questions for Oropouche, created as a preset called **User Generated**.

## Files

   - **Clinical Characterization XML:** This XML file provides a recommended configuration and structure for clinical characterization studies. It includes information about users, events, project settings, and functionality, serving as a reference for setting up clinical characterization studies.

   - **ARC:** The "ARC" file is a machine-readable CSV (Comma-Separated Values) file that forms the core of ARC. It contains a comprehensive list of questions that can be asked in a CRF during outbreaks. Each question is defined with specific parameters, including variable names, coded answers, limits, types, skip logic, and more.

   - **Lists of Standardized Terms:** These files include predefined sets of standardized vocabulary used to describe and categorize various aspects of CRF answers. Standardized terms ensure consistency in data capture, covering items such as comorbidities, symptoms, and medications.

- **Metadata:** For each version of ARC, a version history file is included. This file contains pertinent information about changes made to ARC over time, allowing for easy tracking of modifications. Typical metadata includes the date of upload of the new version and a description of the changes made.

This structured organization facilitates easy access to different versions of ARC, clinical characterization guidelines, standardized terms, and metadata. Users can navigate the repository to find the specific version of ARC they need and explore related resources.

## Version Identification

In a centralized repository structure like ARC, managing version identification is crucial for tracking changes and updates. ARC uses a version numbering system to indicate different levels of updates and changes:

- **Major Version:** The major version number represents significant updates and changes. This may include the addition of new events, forms, or diseases, as well as changes in the functionalities of the CRF.

- **Minor Version:** The minor version number indicates smaller updates and additions. It signifies the inclusion of new features, improvements, or functionality enhancements without changing existing functionality. Changes in definitions and the addition, removal, or modification of questions fall under this category.

- **Patch Version:** The patch version number represents bug fixes, branching patches, writing improvements, or small updates that address issues discovered in previous versions. These updates do not introduce new features or change existing functionality. Patch versions are typically used for corrections of branching logic errors and improvements in the formulation of questions.

## How to Use ARC

If you want to use ARC for your research or study, follow these steps:

1. **Access ARC**: You can download the latest version of ARC from this GitHub repository.

2. **Contributions**: While contributions to the document are limited to authorized users, you can open issues or discussions for questions, suggestions, or clarifications.

3. **Integration with BRIDGE**: If you're using the BRIDGE software tool, it connects to this GitHub repository to access the latest version of ARC for CRF generation.

## Contributors

### Conceptualization
- Laura Merson - [laura.merson@ndm.ox.ac.uk](mailto:laura.merson@ndm.ox.ac.uk)
- Esteban Garcia-Gallo - [esteban.garcia@ndm.ox.ac.uk](mailto:esteban.garcia@ndm.ox.ac.uk)

### Clinical Expertise
- Dhruv Darji - [dhruv.darji@gtc.ox.ac.uk](mailto:dhruv.darji@gtc.ox.ac.uk)
- Amanda Rojek - [amanda.rojek@ndm.ox.ac.uk](mailto:amanda.rojek@ndm.ox.ac.uk)
- Jake Dunning - [jake.dunning@ndm.ox.ac.uk](mailto:jake.dunning@ndm.ox.ac.uk)
- Gail Carson - [gail.carson@ndm.ox.ac.uk](mailto:gail.carson@ndm.ox.ac.uk)

### Technical Expertise
- Sara Duque-Vallejo - [sara.duquevallejo@ndm.ox.ac.uk](mailto:sara.duquevallejo@ndm.ox.ac.uk)
- Tom Edinburgh - [tom.edinburgh@ndm.ox.ac.uk](mailto:tom.edinburgh@ndm.ox.ac.uk)
- Miles Lunn - [miles.lunn@ndm.ox.ac.uk](mailto:miles.lunn@ndm.ox.ac.uk)
- Sadie Kelly - [sadie.kelly@ndm.ox.ac.uk](mailto:sadie.kelly@ndm.ox.ac.uk)

---

**Note**: ARC is maintained by ISARIC. For inquiries, support, or collaboration, please [contact us](mailto:data@isaric.org).

### Complications Section
- Removed the question on “Pleural effusion / ascites”.
- Added a new question on “Ascites”.

### SNOMED and UMLS Codes Update
- Updated SNOMED and UMLS codes for several variables.
