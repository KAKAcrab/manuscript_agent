# Methods

## Data Collection and Datasets

scRNA-seq datasets were obtained from the Gene Expression Omnibus (GEO, https://www.ncbi.nlm.nih.gov/geo/) database, including GSE199515, GSE176078, and GSE161529, comprising 3 normal breast tissue samples and 16 TNBC tumor samples. [**METHOD CITATION NEEDED: GEO database**] Transcriptomic data from GSE25066, including microarray data and corresponding clinical information from 178 TNBC samples, were downloaded from GEO. Bulk transcriptomic data and clinical information for TNBC from the Molecular Taxonomy of Breast Cancer International Consortium (METABRIC) were obtained from the cBioPortal database (http://www.cbioportal.org/). [**METHOD CITATION NEEDED: cBioPortal**] The METABRIC dataset included 320 TNBC patients, and after excluding non-primary breast cancer cases or patients lacking gene expression profiles, 298 primary TNBC patients were selected for subsequent analysis. A total of 807 ubiquitination-related genes were collected from Chen et al. (2024). [**CITATION NEEDED: Ubiquitination gene source**]

## scRNA-seq Data Processing

scRNA-seq data were analyzed using the Seurat package in R. [**METHOD CITATION NEEDED: Seurat**] Sample data were converted to Seurat objects using the CreateSeuratObject function, selecting cells with 200-6000 features expressed in at least three cells. Data filtering and normalization were performed as follows: (1) removal of low-quality cells expressing fewer than 200 genes; (2) identification and exclusion of potential doublets using the DoubletFinder package; [**METHOD CITATION NEEDED: DoubletFinder**] (3) filtering of cells expressing more than 6000 genes or with mitochondrial gene counts exceeding 25% of total gene counts to ensure data quality; (4) normalization of expression matrices using the NormalizeData function in Seurat, followed by identification of the 2000 most variable genes using the "vst" method in FindVariableFeatures; (5) integration of individual datasets using the Harmony method to eliminate batch effects. [**METHOD CITATION NEEDED: Harmony**] This rigorous stepwise approach ensured reproducibility and accuracy of scRNA-seq data preprocessing.

## Dimensionality Reduction, Unsupervised Clustering, and Cell Type Annotation

For integrated data, we used the ScaleData function to scale z-scores for each variable gene and performed principal component analysis on the scaled data. Using the first 50 principal components and a resolution of 0.1, 11 cell clusters were generated through the FindClusters function. For visualization, we further reduced the dimensionality of integrated data using Uniform Manifold Approximation and Projection (UMAP) through the RunUMAP function in Seurat. [**METHOD CITATION NEEDED: UMAP already cited in Results**] To distinguish cell types, we performed preliminary cell type annotation of single-cell data using the SingleR package, [**METHOD CITATION NEEDED: SingleR**] followed by manual annotation and confirmation using marker genes obtained from literature review and querying the CellMarker 2.0 database (http://bio-bigdata.hrbmu.edu.cn/CellMarker/). [**METHOD CITATION NEEDED: CellMarker 2.0**]

## Identification of Differentially Expressed Genes

To analyze characteristics of cell subpopulations, differentially expressed genes (DEGs) were screened using the "FindAllMarkers" function (minimum percentage = 0.25, log fold-change threshold = 0.25, *P* < 0.05).

## Cell-Cell Communication Analysis

To predict intercellular interactions, we calculated cell-cell communication networks for normal tissue and TNBC using the CellChat R package. [**METHOD CITATION NEEDED: CellChat already cited in Results**] Data in Seurat format were used as input, and Normal and TNBC data were extracted separately and formatted to CellChat format using the createCellChat function. CellChat analysis data processing and visualization were completed using default settings.

## Prognostic Model Construction and Validation

T cell DEGs between TNBC and normal samples were first screened from scRNA-seq datasets. Expression matrices of genes at the intersection of these DEGs and the ubiquitination-related gene set were extracted from the GSE58812 dataset, and WGCNA analysis was performed using survival time as the phenotype to further screen gene sets related to TNBC survival time. [**METHOD CITATION NEEDED: WGCNA already cited in Results**] These DEGs were then analyzed for differential expression between control and disease groups (GSE6522 and GSE6594), univariate Cox regression analysis, and Kaplan-Meier analysis to identify potential prognostic DEGs (*P* < 0.05). [**METHOD CITATION NEEDED: Cox regression, KM analysis already cited in Results**] LASSO-Cox analysis was used to obtain representative genes with prognostic value. [**METHOD CITATION NEEDED: LASSO-Cox already cited in Results**] Based on the multi-gene risk score determined by prognostic features, TNBC patients were divided into high-risk and low-risk groups. The predictive ability of prognostic features was evaluated using the area under the ROC curve (AUC) values. Additionally, the prognostic value of the prognostic model was validated using the GSE25066 dataset. Construction and validation of the TNBC T cell prognostic model were primarily completed using the R packages survival, rms, and timeROC. [**METHOD CITATION NEEDED: R packages**]

## Statistical Analysis

All statistical analyses were performed using R version 4.x. [**METHOD CITATION NEEDED: R software**] Differential expression analysis was performed using Wilcoxon rank-sum test for two-group comparisons. Kaplan-Meier survival curves were compared using the log-rank test. Univariate and multivariate Cox proportional hazards regression models were used to evaluate prognostic factors. Time-dependent ROC curves were constructed to assess model performance. A two-sided *P* value < 0.05 was considered statistically significant.

---

## Citation Points Identified for Methods:

1. **GEO database** - Data repository citation
2. **cBioPortal** - Data repository citation
3. **Seurat package** - Primary analysis tool
4. **DoubletFinder** - Quality control tool
5. **Harmony** - Batch correction method
6. **SingleR** - Cell type annotation tool
7. **CellMarker 2.0 database** - Reference database
8. **R software** - Statistical environment
9. **survival, rms, timeROC packages** - Specific R packages

**Note:** Several methods already cited in Results (UMAP, CellChat, WGCNA, Cox regression, LASSO-Cox, KM analysis) - cross-reference these.

**Total new citations needed:** ~9-12 (low density as required for Methods)

**Status:** Initial draft complete. Requires literature coordination for method citations.
