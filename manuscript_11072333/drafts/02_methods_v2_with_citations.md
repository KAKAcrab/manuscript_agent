# Methods

## Data Collection and Datasets

scRNA-seq datasets were obtained from the Gene Expression Omnibus (GEO, https://www.ncbi.nlm.nih.gov/geo/) database<sup>29</sup>, including GSE199515, GSE176078, and GSE161529, comprising 3 normal breast tissue samples and 16 TNBC tumor samples. Transcriptomic data from GSE25066, including microarray data and corresponding clinical information from 178 TNBC samples, were downloaded from GEO. Bulk transcriptomic data and clinical information for TNBC from the Molecular Taxonomy of Breast Cancer International Consortium (METABRIC) were obtained from the cBioPortal database (http://www.cbioportal.org/)<sup>30</sup>. The METABRIC dataset included 320 TNBC patients, and after excluding non-primary breast cancer cases or patients lacking gene expression profiles, 298 primary TNBC patients were selected for subsequent analysis. A total of 807 ubiquitination-related genes were collected from Chen et al. (2024)<sup>4</sup>.

## scRNA-seq Data Processing

scRNA-seq data were analyzed using the Seurat package (version 4.0 or higher) in R<sup>31</sup>. Sample data were converted to Seurat objects using the CreateSeuratObject function, selecting cells with 200-6000 features expressed in at least three cells. Data filtering and normalization were performed as follows: (1) removal of low-quality cells expressing fewer than 200 genes; (2) identification and exclusion of potential doublets using the DoubletFinder package<sup>32</sup>; (3) filtering of cells expressing more than 6000 genes or with mitochondrial gene counts exceeding 25% of total gene counts to ensure data quality; (4) normalization of expression matrices using the NormalizeData function in Seurat, followed by identification of the 2000 most variable genes using the "vst" method in FindVariableFeatures; (5) integration of individual datasets using the Harmony method<sup>33</sup> to eliminate batch effects. This rigorous stepwise approach ensured reproducibility and accuracy of scRNA-seq data preprocessing.

## Dimensionality Reduction, Unsupervised Clustering, and Cell Type Annotation

For integrated data, we used the ScaleData function to scale z-scores for each variable gene and performed principal component analysis on the scaled data. Using the first 50 principal components and a resolution of 0.1, 11 cell clusters were generated through the FindClusters function. For visualization, we further reduced the dimensionality of integrated data using Uniform Manifold Approximation and Projection (UMAP)<sup>5</sup> through the RunUMAP function in Seurat. To distinguish cell types, we performed preliminary cell type annotation of single-cell data using the SingleR package<sup>34</sup>, followed by manual annotation and confirmation using marker genes obtained from literature review and querying the CellMarker 2.0 database (http://bio-bigdata.hrbmu.edu.cn/CellMarker/)<sup>35</sup>.

## Identification of Differentially Expressed Genes

To analyze characteristics of cell subpopulations, differentially expressed genes (DEGs) were screened using the "FindAllMarkers" function with the following parameters: minimum percentage = 0.25, log fold-change threshold = 0.25, *P* < 0.05. Statistical significance was determined using the Wilcoxon rank-sum test.

## Cell-Cell Communication Analysis

To predict intercellular interactions, we calculated cell-cell communication networks for normal tissue and TNBC using the CellChat R package<sup>12</sup>. Data in Seurat format were used as input, and Normal and TNBC data were extracted separately and formatted to CellChat format using the createCellChat function. CellChat analysis data processing and visualization were completed using default settings as described in the original publication.

## Prognostic Model Construction and Validation

T cell DEGs between TNBC and normal samples were first screened from scRNA-seq datasets. Expression matrices of genes at the intersection of these DEGs and the ubiquitination-related gene set were extracted from the GSE58812 dataset, and WGCNA analysis<sup>19</sup> was performed using survival time as the phenotype to further screen gene sets related to TNBC survival time. These DEGs were then analyzed for differential expression between control and disease groups (GSE6522 and GSE6594), univariate Cox regression analysis<sup>20</sup>, and Kaplan-Meier analysis to identify potential prognostic DEGs (*P* < 0.05). LASSO-Cox analysis<sup>21</sup> was used to obtain representative genes with prognostic value. Based on the multi-gene risk score determined by prognostic features, TNBC patients were divided into high-risk and low-risk groups. The predictive ability of prognostic features was evaluated using the area under the ROC curve (AUC) values through time-dependent ROC curve analysis<sup>25</sup>. Additionally, the prognostic value of the prognostic model was validated using the GSE25066 dataset with internal cross-validation<sup>22</sup>. Construction and validation of the TNBC T cell prognostic model were primarily completed using the R packages survival<sup>36</sup>, rms<sup>37</sup>, and timeROC<sup>38</sup>.

## Statistical Analysis

All statistical analyses were performed using R software (version 4.0 or higher, R Foundation for Statistical Computing, Vienna, Austria)<sup>39</sup>. Differential expression analysis was performed using the Wilcoxon rank-sum test for two-group comparisons. Kaplan-Meier survival curves were compared using the log-rank test. Univariate and multivariate Cox proportional hazards regression models<sup>20,26</sup> were used to evaluate prognostic factors. Time-dependent ROC curves were constructed to assess model performance. Nomogram construction and calibration were performed as described previously<sup>27,28</sup>. A two-sided *P* value < 0.05 was considered statistically significant for all tests.

---

## New References for Methods Section

29. Barrett T, Wilhite SE, Ledoux P, et al. NCBI GEO: archive for functional genomics data sets--update. *Nucleic Acids Res* 2013;41(Database issue):D991-995.

30. Cerami E, Gao J, Dogrusoz U, et al. The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data. *Cancer Discov* 2012;2(5):401-404.

31. Hao Y, Hao S, Andersen-Nissen E, et al. Integrated analysis of multimodal single-cell data. *Cell* 2021;184(13):3573-3587.e29.

32. McGinnis CS, Murrow LM, Gartner ZJ. DoubletFinder: Doublet Detection in Single-Cell RNA Sequencing Data Using Artificial Nearest Neighbors. *Cell Syst* 2019;8(4):329-337.e4.

33. Korsunsky I, Millard N, Fan J, et al. Fast, sensitive and accurate integration of single-cell data with Harmony. *Nat Methods* 2019;16(12):1289-1296.

34. Aran D, Looney AP, Liu L, et al. Reference-based analysis of lung single-cell sequencing reveals a transitional profibrotic macrophage. *Nat Immunol* 2019;20(2):163-172.

35. Hu C, Li T, Xu Y, et al. CellMarker 2.0: an updated database of manually curated cell markers in human/mouse and web tools based on scRNA-seq data. *Nucleic Acids Res* 2023;51(D1):D870-D876.

36. Therneau TM. A Package for Survival Analysis in R. R package version 3.2-13. 2021. https://CRAN.R-project.org/package=survival

37. Harrell FE Jr. rms: Regression Modeling Strategies. R package version 6.2-0. 2021. https://CRAN.R-project.org/package=rms

38. Blanche P, Dartigues JF, Jacqmin-Gadda H. Estimating and comparing time-dependent areas under receiver operating characteristic curves for censored event times with competing risks. *Stat Med* 2013;32(30):5381-5397.

39. R Core Team. R: A Language and Environment for Statistical Computing. R Foundation for Statistical Computing, Vienna, Austria. 2021. https://www.R-project.org/

---

**Metadata:**
- Word count: ~650 words
- New method citations: 11 (refs 29-39)
- Cross-referenced from Results: 9 (refs 4, 5, 12, 19-22, 25-28)
- Total references used: 20
- Citation density: Low (as required for Methods section)
- Status: Ready for quality control
