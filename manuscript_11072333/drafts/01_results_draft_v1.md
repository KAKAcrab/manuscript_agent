# Results

## Single-cell transcriptomic landscape reveals cellular heterogeneity in TNBC

To characterize the cellular composition of triple-negative breast cancer (TNBC), we integrated single-cell RNA sequencing (scRNA-seq) data from 3 normal breast tissue samples and 16 TNBC tumor samples, comprising a total of 84,837 cells after rigorous quality control and batch effect correction. Uniform Manifold Approximation and Projection (UMAP) dimensionality reduction identified 11 distinct cell clusters (**Figure 1A**). Cell type annotation was performed using established marker genes and cluster-specific top expressed genes, revealing the following cell populations: Epithelial cells (cluster 0, expressing *KRT23* and *KRT15*), T cells (cluster 1, *CD3D*, *TRBC2*, *CD3E*), Proliferating Epithelial cells (cluster 2, *MKI67*, *TOP2A*), Macrophages (cluster 3, *CD68*, *CD14*), Fibroblasts (cluster 4, *DCN*, *LUM*), Basal cells (cluster 5, *KRT5*, *KRT14*), Endothelial cells (cluster 6, *PECAM1*, *PLVAP*), Luminal Epithelial cells (cluster 7, *KRT18*, *ANKRD30A*), Plasma cells (cluster 8, *IGHG1*, *IGHG4*), Pericytes (cluster 9, *RGS5*, *COX4I2*), and B cells (cluster 10, *MS4A1*, *BANK1*) (**Figure 1B, C**).

Comparative analysis of cell type proportions between normal and TNBC tissues revealed substantially elevated infiltration of immune cells in tumor samples, particularly B cells, T cells, and Macrophages (**Figure 1D**). Differential expression analysis across all 11 cell types identified cell type-specific transcriptional changes between TNBC and normal tissues. Notably, T cells exhibited significant upregulation of *IGLV1*, *TRBV20-1*, and *ATP5E* in TNBC samples (adjusted *P* < 0.01) (**Figure 1E**).

Gene Ontology (GO) enrichment analysis of upregulated genes revealed widespread activation of immune-related pathways in TNBC tumors. Antigen processing and presentation pathways, including antigen processing and presentation, antigen processing and presentation of peptide antigen, and MHC protein complex assembly, were significantly enriched across all 11 cell types (adjusted *P* < 0.01), suggesting enhanced antigen presentation activity in the TNBC tumor microenvironment. [**CITATION NEEDED: Studies showing enhanced antigen presentation in TNBC**] T cell-related functional pathways, including T cell proliferation, lymphocyte mediated immunity, positive regulation of T cell activation, and positive regulation of lymphocyte activation, were upregulated in multiple cell types, indicating active T cell immune responses in the TNBC microenvironment. Notably, these immune activation signals were observed not only in immune cell populations (B cells, T cells, Plasma cells, and Macrophages) but also in stromal cells such as Endothelial cells and Fibroblasts, suggesting coordinated regulation of T cell immunity across diverse cell types in the tumor microenvironment. Additionally, upregulation of positive regulation of cell adhesion and antigen receptor-mediated signaling pathway may reflect enhanced T cell recruitment, infiltration, and interaction with antigen-presenting cells.

In contrast, downregulated genes were predominantly enriched in basic metabolic and cellular homeostasis pathways, including regulation of translation, ribosomal small subunit biogenesis, response to oxidative stress, cellular response to reactive oxygen species, and regulation of apoptotic signaling pathway. [**CITATION NEEDED: Studies on metabolic dysfunction in tumor stroma**] Endothelial cells and Fibroblasts exhibited the most extensive downregulation patterns. This "T cell immune activation-stromal metabolic suppression" dual regulatory mode reveals the complexity of the TNBC tumor microenvironment, where stromal cell metabolic dysfunction may impact T cell anti-tumor efficacy through nutrient competition and metabolite accumulation mechanisms. [**CITATION NEEDED: T cell exhaustion and metabolic competition in TME**]

## Enhanced intercellular communication networks in TNBC microenvironment

To elucidate bidirectional communication between T cells and other cell types in the TNBC microenvironment, we performed ligand-receptor interaction analysis using CellChat. Comparison of interaction patterns between normal and TNBC samples revealed increased signaling between immune cells (T cells, B cells, and Macrophages) and other cell types in TNBC, with substantially higher numbers of interactions in tumor tissues (**Figure 2A-D**). Overall, 87 signaling pathways participated in constructing the intercellular communication network in TNBC, including 12 normal-specific pathways, 31 TNBC-specific pathways, and 44 shared pathways (**Figure 2E**).

Analysis of incoming and outgoing signal interaction strengths in two-dimensional space demonstrated that T cells in TNBC exhibited enhanced bidirectional signaling compared to normal tissues, with particularly elevated incoming signal strength (**Figure 2F, G**). [**CITATION NEEDED: Studies on T cell signaling in TNBC**] Focused examination of T cell input and output signaling changes identified unique alterations in MHC-I, MIF, and CD99 pathways in TNBC (**Figure 2H**). In TNBC samples, nine secretory ligand-expressing cell types interacted with T cells through MIF, CXCL, CCL, and COMPLEMENT pathways, mediated by multiple ligand-receptor pairs including MIF-(CD74+CD44), MIF-(CD74+CXCR4), CXCL12-CXCR4, and CXCL10-CXCR3 (**Figure 2I**). [**CITATION NEEDED: MIF signaling in T cell recruitment and activation**] When T cells functioned as signal senders, three receiver cell types were identified: B cells, Macrophages, and Endothelial cells (**Figure 2J**). MIF-(CD74+CD44) and MIF-(CD74+CXCR4) represented common ligand-receptor pairs between T cells and all nine cell types, while CXCL10-CXCR3 may serve as a specific communication pathway between Macrophages and T cells. [**CITATION NEEDED: CXCL10-CXCR3 axis in macrophage-T cell crosstalk**]

## Identification of ubiquitination-related prognostic genes through integrated analysis

Recognizing the critical role of T cells in TNBC progression, we identified 3,067 T cell-associated genes. Given that ubiquitination profoundly influences cellular growth, differentiation, cell cycle regulation, apoptosis, and cancer development, [**CITATION NEEDED: Role of ubiquitination in cancer biology**] we extracted 807 ubiquitination-related genes (Chen et al., 2024). Intersection of these two gene sets yielded 177 T cell-related ubiquitination genes (TCRUG) (**Figure 3A**).

Weighted gene co-expression network analysis (WGCNA) of TCRUG revealed four distinct modules (**Figure 3B**). The MEturquoise module exhibited the strongest correlation with survival time (correlation coefficient = 0.002, *P* < 0.01), suggesting that genes in this module may be closely associated with TNBC patient prognosis (**Figure 3C**). Differential expression analysis of 61 genes within the MEturquoise module identified 59 significantly differentially expressed genes between tumor and normal tissues (*P* < 0.05). Integration with Kaplan-Meier survival analysis (*P* < 0.05, 21 genes) and univariate Cox regression analysis (*P* < 0.05, 30 genes) (**Figure 3D-F**) identified 13 genes common to all three analytical approaches, designating them as key prognostic candidates (**Figure 3G**).

## Construction and validation of a three-gene prognostic risk model

Application of LASSO-Cox regression analysis to the 13 candidate genes identified three key genes—*GMCL1*, *KRT8*, and *OTUB1*—for prognostic model construction. [**CITATION NEEDED: LASSO-Cox for biomarker selection in cancer prognosis**] To comprehensively validate the model's prognostic predictive performance, we partitioned the TCGA dataset into training and test sets using the R package "caret" and incorporated the GSE25066 dataset as an external validation cohort. Kaplan-Meier analysis demonstrated that patients with high risk scores exhibited significantly worse prognosis across all three datasets (log-rank *P* < 0.0001 for TCGA-Train, *P* = 0.00019 for TCGA-Test, *P* = 0.0023 for GSE25066) (**Figure 4A-C**).

Comprehensive comparative analysis revealed that high-risk group patients exhibited significantly elevated mortality rates compared to low-risk group patients. Heatmap analysis demonstrated distinct expression patterns of the modeling genes: *KRT8* and *OTUB1* were significantly upregulated in the high-risk group, while *GMCL1* exhibited the opposite pattern (**Figure 4D-F**). [**CITATION NEEDED: Biological roles of GMCL1, KRT8, OTUB1 in cancer**]

## Independent prognostic value and clinical nomogram construction

To evaluate the risk model's classification performance, we performed time-dependent ROC curve analysis. In the TCGA-Train cohort, the area under the curve (AUC) values for 2-year, 3-year, and 5-year survival predictions were 0.67, 0.69, and 0.72, respectively. The TCGA-Test cohort yielded AUC values of 0.53, 0.63, and 0.70, while the GSE25066 validation cohort demonstrated AUC values of 0.62, 0.63, and 0.59 (**Figure 5A-C**).

To investigate the relationship between risk scores and clinical features, we conducted univariate and multivariate Cox regression analyses. Univariate analysis identified T stage, N stage, and risk score as significant prognostic factors. Importantly, multivariate Cox regression confirmed the risk score as an independent prognostic factor (hazard ratio = 8.881, *P* = 0.003) after adjusting for T and N stages (**Figure 5D, E**). [**CITATION NEEDED: Independent prognostic factors in TNBC**]

Considering that integration of clinical parameters with risk scores may enhance prognostic accuracy, we constructed a nomogram incorporating age, T stage, grade, N stage, and risk score to predict 1-year, 3-year, and 5-year survival probabilities (**Figure 5F**). Calibration curves validated the nomogram's robust predictive performance (**Figure 5G**). ROC curve analysis demonstrated that the nomogram achieved superior predictive performance (AUC = 0.719) compared to individual clinical factors (**Figure 5H**). Kaplan-Meier analysis stratified by nomogram scores confirmed that patients with high nomogram scores exhibited significantly worse prognosis (*P* = 0.00034) (**Figure 5I**). [**CITATION NEEDED: Nomograms for TNBC prognosis prediction**]

---

## Temporary Reference List (To be replaced with full citations after literature coordination)

1. Chen C, Chen Z, Zhou Z, Ye H, Xiong S, Hu W, Xu Z, Ge C, Zhao C, Yu D, Shen J (2024) T cell-related ubiquitination genes as prognostic indicators in hepatocellular carcinoma. Frontiers in Immunology 15. doi:10.3389/fimmu.2024.1424752

---

**Notes for literature coordination:**
- Total citation points identified: 10
- Citation density: Medium (approximately every 3-5 sentences in discussion-heavy sections)
- Key topics requiring literature support:
  1. Enhanced antigen presentation in TNBC
  2. Metabolic dysfunction in tumor stroma
  3. T cell exhaustion and metabolic competition in TME
  4. T cell signaling pathways in TNBC
  5. MIF signaling in T cell recruitment
  6. CXCL10-CXCR3 axis in immune cell crosstalk
  7. Ubiquitination in cancer biology
  8. LASSO-Cox for biomarker selection
  9. Biological roles of GMCL1, KRT8, OTUB1
  10. Independent prognostic factors and nomograms in TNBC

**Status:** Initial draft complete. Requires literature coordination (Phase 2) and quality control (Phase 3) before finalization.
