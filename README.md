# ARC - Analysis and Research Compendium

ISARIC ARC is a comprehensive library of questions that can be used to rapidly build standardised Case Report Forms (CRFs) for disease outbreaks. It covers a wide range of patient-related information, including demographics, comorbidities, signs and symptoms, medications, outcomes, and more. Each question in ARC has specific guidelines and relevant parameters, such as definitions, answer options, units, minimum and maximum limits, data types, skip logic, and more. 

## About ARC

ARC (Analysis and Research Compendium) is designed to serve as a resource for researchers and healthcare professionals involved in the study of outbreaks and emerging public health threats. Here's what you need to know:

- **Machine-Readable**: ARC is provided in CSV format, making it easy for automated systems to read and process the data.

- **Open Access**: ARC is made openly available for the research community. While contributions are limited to authorized individuals, the document can be freely accessed and utilized by others.

- **Version Control**: We continue to improve ARC by adding new questions and implementing structural changes. We maintain a comprehensive history of changes made to ARC using GitHub's version control. This ensures document integrity, traceability of changes, and seamless collaboration among researchers. Previous ARC versions may be accessed via this [repository’s releases](https://github.com/ISARICResearch/ARC/releases). Additional questions can be added to future ARC versions by contacting us at: [data@isaric.org](mailto:data@isaric.org).

- **Integration with the Clinical Epidemiology Platform**: ARC is integrated into [BRIDGE](https://github.com/ISARICResearch/BRIDGE), our software tool for CRF generation.

## ARChetype CRFs and Templates

ISARIC works closely with experts around the world to create CRFs for priority emerging and infectious diseases and outbreak-related syndromes. These CRFs address key clinical research questions that can improve patient outcomes. We call these ARChetype CRFs.

ARChetype CRFs are an important subset of our library of Templates. Templates are sets of ARC questions that we have curated for other outbreak-related contexts, such as clinical severity scores and core outcome sets. The library of Templates is openly available for use and adaptation by the research community. More information about how to download an ARChetype CRF can be found in our [Downloading an ARChetype CRF Guide](https://isaricresearch.github.io/Training/bridge_template_link).

## ARC Version 1.1.3
ARC Version 1.1.3 contains a library of questions to be used in Case Report Forms (CRFs) tailored for outbreak responses for COVID-19, Dengue, Mpox and H5Nx and ARI. The CRFs are grouped into seven forms, ‘presentation’, ‘daily’, ‘medication’, ‘pathogen testing’, ‘outcome’,‘follow up’ and ‘withdrawal’ which contain several sections including questions about inclusion and exclusion criteria, hospital admission, patient demographics, travel history, exposure history, pregnancy- and infant-related questions, comorbidities and risk factors, past medical history, medication (drug) history, vaccination history, vital signs assessment, signs and symptoms, clinical assessment, treatment and interventions, laboratory results, imaging results, pathogen testing as well as complications. The questions comprehensively capture the relevant information from the time of presentation to the health facility, daily assessment during admission and at the discharge from the health facility. 

ARC Version 1.1.3 contains the following ARChetype CRFs and Templates, each grouped within the forms and sections described above:
   - **COVID-19 ARChetype CRF:** In ARC Version 1.1.3, this contains 444 questions for COVID-19 outbreak responses. 
   - **Dengue ARChetype CRF:** In ARC Version 1.1.3, this contains 445 questions for Dengue outbreak responses.
   - **Mpox ARChetype CRF:** In ARC Version 1.1.3, this contains 595 questions for Mpox outbreak responses. This ARChetype CRF has a section on skin and mucosal assessment for Mpox lesions. 
   - **H5Nx ARChetype CRF:** In ARC Version 1.1.3, this contains 524 question for Influenza H5Nx outbreak responses.
   - **ARI  ARChetype CRF:** In ARC Version 1.1.3, this contains 575 question for Acute Respiratory Infection outbreak responses.
   - **Dengue Recommended Outcomes:**  In ARC Version 1.1.3, this contains 79 question for for Dengue outbreak responses.


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

2. **Integration with BRIDGE**: If you use the [BRIDGE](https://github.com/ISARICResearch/BRIDGE) software tool, it connects to this GitHub repository to access all releases of ARC for CRF generation.

3. **Contributions**: While contributions to the document are limited to authorized users, you can open issues or discussions for questions, suggestions, or clarifications.

## Contributors

### Conceptualization
- Laura Merson - [laura.merson@ndm.ox.ac.uk](mailto:laura.merson@ndm.ox.ac.uk)
- Esteban Garcia-Gallo - [esteban.garcia@ndm.ox.ac.uk](mailto:esteban.garcia@ndm.ox.ac.uk)

### Clinical Expertise
- Dhruv Darji - [dhruv.darji@gtc.ox.ac.uk](mailto:dhruv.darji@gtc.ox.ac.uk)
- Amanda Rojek - [amanda.rojek@ndm.ox.ac.uk](mailto:amanda.rojek@ndm.ox.ac.uk)
- Jake Dunning - [jake.dunning@ndm.ox.ac.uk](mailto:jake.dunning@ndm.ox.ac.uk)
- Gail Carson - [gail.carson@ndm.ox.ac.uk](mailto:gail.carson@ndm.ox.ac.uk)
- Luis Felipe Reyes - [luis.reyes@ndm.ox.ac.uk](mailto:luis.reyes@ndm.ox.ac.uk)
- Claudia Figueiredo Mello - [claudia.mello@emilioribas.sp.gov.br](mailto:claudia.mello@emilioribas.sp.gov.br)
- Lauren Sauer - [lsauer@unmc.edu](mailto:lsauer@unmc.edu)
- Mattew Cummings - [mjc2244@cumc.columbia.edu](mailto:mjc2244@cumc.columbia.edu)
- Peter Horby - [peter.horby@ndm.ox.ac.uk](mailto:peter.horby@ndm.ox.ac.uk)
- Janet Diaz (WHO) - [diazj@who.int](mailto:diazj@who.int)
- Jamie Rylance (WHO) - [rylancej@who.int](mailto:rylancej@who.int)
- Calum Semple - [M.G.Semple@liverpool.ac.uk](mailto:M.G.Semple@liverpool.ac.uk)
- Lim Wei Shen - [WeiShen.Lim@nuh.nhs.uk](mailto:WeiShen.Lim@nuh.nhs.uk)
- Srin Murthy - [srinivas.murthy@cw.bc.ca](mailto:srinivas.murthy@cw.bc.ca)
- Antonia Ho - [antonia.ho@glasgow.ac.uk](mailto:antonia.ho@glasgow.ac.uk)
- Tim Uyeki - [tmu0@cdc.gov](mailto:tmu0@cdc.gov)

### Technical Expertise
- Sara Duque-Vallejo - [sara.duquevallejo@ndm.ox.ac.uk](mailto:sara.duquevallejo@ndm.ox.ac.uk)
- Tom Edinburgh - [tom.edinburgh@ndm.ox.ac.uk](mailto:tom.edinburgh@ndm.ox.ac.uk)
- Elise Pesonel - [elise.pesonel@ndm.ox.ac.uk](mailto:elise.pesonel@ndm.ox.ac.uk)
- Miles Lunn - [miles.lunn@ndm.ox.ac.uk](mailto:miles.lunn@ndm.ox.ac.uk)
- Sadie Kelly - [sadie.kelly@ndm.ox.ac.uk](mailto:sadie.kelly@ndm.ox.ac.uk)

---

**Note**: ARC is maintained by ISARIC. For inquiries, support, or collaboration, please [contact us](mailto:data@isaric.org).
