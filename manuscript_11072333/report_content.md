**材料与方法**

**数据收集**

本研究从基因表达综合数据库（GEO，http:
//www.ncbi.nlm.nih.gov/geo/）下载了GSE199515、GSE176078和GSE161529乳腺癌scRNA-seq数据集，这些数据集中包含3个Normal样本和16个TNBC样本。我们还从GEO下载了转录组数据gse25066的微阵列数据及其TNBC样本相应的临床数据，该数据集包含178例TNBC样本。此外，我们从cBioPortal数据库（
http://www.cbioportal.org/
）下载了乳腺癌分子分类国际联盟（METABRIC）的批量转录组数据和三阴性乳腺癌（TNBC）的临床信息。METABRIC数据集包含320例TNBC患者，排除了非原发性乳腺癌病例或缺乏基因表达谱的患者，最终筛选出298例原发性TNBC患者进行后续分析。我们从(Chen
et al. 2024)搜集了807个泛素化相关的基因。

**ScRNA-seq测序数据处理**

利用R软件中Seurat包的"CreateSeuratObject"函数分析本研究收集的scRNA-seq数据，首先样本数据转换为Seurat对象，筛选出包含nfeature大于等于200小于6000个特征且基因在三个以上细胞中共享的细胞(Fig.
S1
A,B)。数据过滤和标准化步骤如下：（1）去除低质量细胞，即去除表达基因少于200个；（2）使用DoubletFinder包识别并排除潜在的双细胞；（3）过滤掉表达基因超过6000个以及线粒体基因计数超过总基因数25%的细胞，以确保数据质量；（4）使用
Seurat的 NormalizeData 函数对表达矩阵进行标准化，然后使用
FindVariableFeatures 中的"vst"方法识别出变异性最高的 2000
个基因；（5）使用harmony方法进一步整合个体数据，以消除样本间的批次效应。这种严谨的逐步方法确保了scRNA-seq数据预处理的可重复性和准确性。

**降维和无监督聚类以及细胞簇的注释**

对于整合后的数据，我们使用 ScaleData 函数对每个可变基因的 z
分数进行缩放，并对缩放后的数据进行主成分分析。使用前
50个主成分和0.1的分辨率，通过 FindClusters
函数生成11个细胞簇。为了便于可视化，我们使用 Seurat 的 RunUMAP
函数，通过均匀流形逼近和投影 (UMAP)
方法进一步降低整合后数据的维度。为了进一步区分细胞类型，我们使用SingleR软件包对单细胞数据进行初步的细胞类型注释，然后通过查阅文献和检索CellMarker
2.0数据库（http://bio-bigdata.hrbmu.edu.cn/CellMarker/）获得的细胞marker
genes人工手动注释的再次确认。

**免疫相关差异表达基因的鉴定**

为了分析各细胞亚群的特征，使用"FindAllMarkers"函数筛选差异表达基因（DEGs）（最小百分比=0.25，logfc阈值=0.25，P\<0.05）。

**细胞间通讯分析**

为了预测细胞间的相互作用，我们使用 CellChat R
包计算了正常组织和TNBC（triple-negative breast
cancer）的细胞间通讯网络。首先，我们将为Seurat
格式的数据为输入，并分别提取了Normal和TNBC的数据，并使用createCellChat函数将其格式化为
CellChat 格式。最后，我们使用默认设置完成了 CellChat
分析的数据处理和可视化。

**预测模型构建与验证**

首先，我们从scRNA-seq数据集中筛选出TNBC和正常样本中的T细胞差异表达基因（DEGs）。然后，提取GSE58812数据集中这些DEGs与泛素化相关的基因集的交集基因的表达矩阵，并以数据集中样本对应的生存时间为表型进行WGCNA分析，进一步筛选与TNBC生存时间相关的基因集。然后，分别分析这些DEGs在对照和疾病组的差异表达（GSE6522和GSE6594）、单因素Cox回归分析以及KM分析，以识别潜在的预后DEGs（
P \<
0.05）。使用lasso_cox分析得到具有预后价值的代表基因。最后，根据预后特征确定的多基因风险评分，将TNBC患者分为高风险组和低风险组。我们使用ROC曲线下面积（AUC）值评估了预后特征的预测能力。此外，我们使用GSE25066数据集验证了预后模型的预后价值。TNBC
T细胞预后模型的构建和验证主要使用R语言的survival、rms和timeROC包完成。

**结果与分析**

**TNBC的scRNA-seq图谱构建**

为了了解三阴乳腺癌的细胞构成，我们利用公共数据库收集了的3例Normal样本和16例TNBC样本的scRNA-seq数据（附表1）。经过严格的质量控制以及去除样本间的批次效应，最终我们将84837个细胞通过均匀流形逼近和投影（UMAP）分为了11个Cluster（Figure1
A）。根据已建立的细胞类型标记基因和不同cluster的top基因（FS1，C）对细胞簇进行注释（Figure1
B）：KRT23和KRT15在Epithelial（cluster0）高表达；CD3D、TRBC2和CD3E的特异高表达代表T细胞（cluster1）;MKI67和TOP2A代表Proliferating
Epithelial（cluster2）;
CD68和CD14的特异高表达代表Macrophages（cluster3）；DCN和LUM的特异高表达Fibroblasts（cluster4）；KRT5和KRT14的高表达Basal
（cluster5）; PECAM1和PLVAP的特异高表达Endothelial （cluster6）;
KRT18和ANKRD30A的高表达 Luminal Epithelial （cluster7）;
IGHG1和IGHG4的特异高表达Plasma cell（cluster8）;
RGS5和COX4I2的特异高表达Pericytes（cluster9）; MS4A1和BANK1的特异高表达B
cells（cluster10）。最终得到11种特定的细胞类型（figure1
C）。随后，我们比较了11种细胞类型在正常组织和TNBC肿瘤组织中的比例差异，肿瘤组织中多种免疫细胞类型的数量明显更多，比如B细胞、T细胞和Macrophages（figure1
D, figureS2
A）。这一观察结果可能与TNBC样本中增强的免疫浸润有关。此外，我们还使用FindMarkers()函数鉴定了11种细胞类型在Normal和TNBC样本中的差异表达基因，其中T细胞中IGLV1、TRBV20-1和ATP5E等基因在TNBC中具有更显著的高表达（figure1
E）。为了系统解析TNBC与正常乳腺组织中不同细胞类型的功能变化特征，我们对差异表达基因进行了GO富集分析，并通过气泡图展示了跨细胞类型的富集模式（图FS2-B）。结果显示，TNBC组织中上调基因主要富集于免疫相关通路，其中抗原处理与呈递（antigen
processing and presentation）、抗原肽段加工与呈递（antigen processing
and presentation of peptide antigen）以及MHC蛋白复合物组装（MHC protein
complex assembly）在所有11种细胞类型中均呈现显著富集（p.adjust \<
0.01），提示TNBC肿瘤微环境中存在广泛的免疫激活和抗原呈递活性增强。特别值得关注的是，T细胞增殖（T
cell proliferation）、淋巴细胞介导的免疫反应（lymphocyte mediated
immunity）、T细胞活化正调控（positive regulation of T cell
activation）以及淋巴细胞活化正调控（positive regulation of lymphocyte
activation）等T细胞相关功能通路在多数细胞类型中显著上调，表明TNBC肿瘤微环境中存在活跃的T细胞免疫反应。这种广泛的抗原呈递和T细胞活化信号不仅在免疫细胞亚群（B细胞、T细胞、浆细胞和巨噬细胞）中富集，在内皮细胞、成纤维细胞等基质细胞中也呈现上调趋势，提示肿瘤微环境中多种细胞类型参与协同调控T细胞免疫反应。此外，细胞粘附正调控（positive
regulation of cell adhesion）和抗原受体介导的信号通路（antigen
receptor-mediated signaling
pathway）的上调可能反映了T细胞向肿瘤组织的募集、浸润以及与抗原呈递细胞的相互作用过程增强。与免疫激活形成鲜明对比，下调基因主要富集于基础代谢和细胞稳态维持相关通路，包括翻译调控（regulation
of translation）、核糖体小亚基生物合成（ribosomal small subunit
biogenesis）、氧化应激反应（response to oxidative
stress）、活性氧应激反应（cellular response to reactive oxygen
species）以及凋亡信号通路调控（regulation of apoptotic signaling
pathway）等。值得注意的是，内皮细胞和成纤维细胞在下调通路中表现出最广泛的富集模式，而这些基质细胞代谢功能的抑制和氧化应激的增强可能对T细胞的功能状态产生重要影响。这种\"T细胞免疫激活-基质代谢抑制\"的双向调控模式揭示了TNBC肿瘤微环境的复杂性：一方面通过增强抗原呈递和T细胞活化形成抗肿瘤免疫反应，另一方面基质细胞的功能失调可能通过营养竞争、代谢物积累等机制影响T细胞的抗肿瘤效应，这些发现为进一步研究TNBC中T细胞的功能状态、耗竭机制以及开发基于T细胞的免疫治疗策略提供了重要的理论基础。

![](media/image1.png){width="5.768055555555556in" height="6.725in"}

Figure1 通过整合三阴乳腺癌scRNA-seq数据识别其主要细胞簇。

\(A\) 对19个样本中84837个细胞进行 scRNA-seq 分析并整合后的 UMAP
可视化结果。从左到右分别按不同样本，不同group和不同cell cluster着色。

\(B\) Dotplot图展示了不同细胞类型标记基因在每个cell
cluster中的表达情况。

\(C\) UMAP图展示了通过标记基因识别出的主要细胞类型

(D)堆积柱形图展示Normal和TNBC中不同细胞类型的占比

\(E\)
TNBC和normal样本中不同细胞类型的差异表达火山图。图中对每个细胞类型中差异变化最大top10基因进行了标注。红色的点代表padj\<0.01，黑色点代表padj\>=0.01。

**TNBC中不同细胞类型间的细胞通讯分析**

为了阐明T细胞等免疫细胞与其他细胞类型之间的双向通讯，我们利用CellChat软件探索了它们之间潜在的ligand--receptor相互作用。Normal和TNBC中的不同细胞类型之间相互作用数量和强度差异结果显示，与Noamal相比，TNBC中T细胞、B细胞和Macrophages等免疫细胞与其他细胞类型之间的信号增加，而且TNBC中相互作用的数量明显更多（Figure
2
A-D）。总体而言，共有87条通路（XXX个基因）参与构建三阴乳腺癌微环境的细胞间通讯网络，其中包括12个在Normal中特异性通路和31个在TNBC中特异性通路以及44个共有通路（Figure
2
E）。通过对比在二维空间中Normal和TNBC中细胞之间传入和传出信号相互作用强度的变化，我们发现相较于Normal，TNBC中的T细胞传入和传出信号相互作用的强度更强，尤其是输入信号（Figure2
F-G）。因此，我们重点关注了T细胞在TNBC和Normal间输入输出的信号变化，结果发现MHC−I、MIF和CD99在TNBC中发生了独特的信号改变（Figure2
H）。在TNBC样本中，9种分泌配体的细胞通过MIFCXCL、CCL以及COMPLEMENT通路与T细胞相互作用，这一过程由多种配体-受体对介导，例如MIF−(CD74+CD44)、MIF−(CD74+CXCR4)、CXCL12−CXCR4和CXCL10−CXCR3（Figure2
I）。当T细胞作为信号发送者时，有3种细胞接收者与其相互作用：B细胞、Macrophages和Endothelial（Figure2
J）。MIF−(CD74+CD44)和MIF−(CD74+CXCR4)是T细胞与其他9种细胞都有的配体-受体对，而CXCL10
−
CXCR3可能作为Macrophages与T细胞通讯的特异性配体-受体对。综上所述，我们构建了正常样本和三阴乳腺癌样本的细胞间通讯网络，加深了对T细胞其他细胞串扰通路的理解。

![](media/image2.png){width="5.768055555555556in"
height="7.303472222222222in"}

Fig2 TNBC和normal样本中11中细胞类型间细胞通讯

\(A\)
Circle图展示了TNBC和normal中不同细胞类型之间相互作用数量差异。红色（蓝色）edges表示与Normal相比，TNBC中的信号增加（减少）。(B)
Circle图展示了TNBC和normal中不同细胞类型之间相互作用强度差异。红色（蓝色）边缘表示与Normal相比，TNBC中的信号增加（减少）。(C)
Normal样本不同细胞类型间通讯网络相互作用的数量。线条数量代表相互作用的数量，线条的粗细与相互作用的强度成正比。(D)
TNBC样本中不同细胞类型间通讯网络相互作用的数量。线条数量代表相互作用的数量，线条的粗细与相互作用的强度成正比。
(E)
堆叠条形图显示每个信号通路的整体信息流。垂直虚线表示样本占整体信息流的50%的位置。(F)
散点图显示了Normal样本在二维空间中的主要senders and receivers。(G)
散点图显示了TNBC样本在二维空间中的主要senders and
receivers。（H）散点图展示了Normal和TNBC样本中与T细胞相关的信号变化。**（I）点阵图展示了从**senders**（其他细胞）到T细胞的**MIF、CXCL、CCL以及COMPLEMENT中显著配体-受体对的表达。P值根据CellChat软件的单侧置换检验计算得到，热图颜色代表通讯概率的大小。
（J）**点阵图**显示从**T细胞**到细胞receivers（B细胞、Macrophages和Endothelial）的MIF、CXCL、CCL以及COMPLEMENT中显著配体-受体对的表达。P值根据CellChat软件的单侧置换检验计算得到，热图颜色代表通讯概率的大小。

**WGCNA结合差异表达分析和预后分析识别与泛素化相关的关键基因**

鉴于T细胞在三阴乳腺癌发生发展中的关键作用，我们筛选了3067个与T细胞密切相关的基因。泛素化作为蛋白质合成后的重要生化过程，通过对氨基酸残基进行化学修饰，深刻影响细胞生长、分化、细胞周期调控、细胞凋亡和癌症发生等生物学过程。我们提取了807个与泛素化修饰密切相关的关键基因(Chen
et al.
2024)\[REF\]。通过比较两组关键基因，我们鉴定出177个共有基因，并将其定义为TCRUG（T
cell-related ubiquitination genes）（Figure 3
A,TableS2）。这些基因可能在T细胞功能和泛素化修饰过程中均发挥重要作用。为了更深入地探究TCRUG在TNBC中的功能网络，我们对其进行了WGCNA分析。结果显示样本被清晰地划分为4个模块（Figure
3
B）。其中，我们发现MEturquoise模块与生存时间高度相关，该模块中的基因表达可能与TNBC患者的预后密切相关（Figure
3
C）。之后，我们对该模块内的61个基因进行了差异表达分析（P\<0.05）得到59个显著差异的基因、Kaplan-Meier生存分析（P\<0.05）和Cox回归分析（P\<0.05）分别得到21、30个基因，以揭示其在TNBC发生发展中的潜在机制（Figure
3
D-F）。最后，通过整合上述分析结果，我们鉴定了13个共同基因，这些基因将作为后续研究的重点（Figure
3 G）。

![](media/image3.png){width="5.768055555555556in" height="8.29375in"}

Figure3 WGCNA结合差异表达分析和预后分析识别与泛素化相关的关键基因。

（A）Venn图展示了
T细胞DEGs和泛素蛋白酶体系统基因基因的交集。（B）基因树状图显示177个交集基因被很好地聚类为4类。（C）热图显示了4个基因模块与生存时间的相关性。图例颜色代表相关性的大小，括号中的数值代表显著性P值。（D）热图展示了MEturquoise模块基因在癌组织和正常组织中的差异表达基因的相对表达水平。（E）COX分析显示23个具有预后价值的基因。（F）KM分析显示21个具有预后价值基因。（G）UpSet图显示了差异表达分析、KM分析和COX分析的交集，共包含13个基因。

**LASSO-COX算法构建风险预后模型并进行验证**

通过应用lasso-cox算法，我们从上述交叉基因中准确筛选出3个关键基因------GMCL1、KRT8以及OTUB1(FS3A,B)，并利用这些基因构建了预后模型。由于风险评分与患者预后密切相关，我们采用了三个不同的数据集来全面验证该模型的预后预测效能。利用R语言包"caret"，我们将TCGA数据集划分为训练集和验证集，并引入GSE25066数据集作为额外的验证集。分析结果表明，在这三个数据集中，高风险评分患者的预后趋势均较差（Figure
4
A-C）。为了进一步探究不同风险组的生存结局，我们进行了全面的比较分析。研究结果表明，高危组患者的死亡率显著高于低危组患者。此外，热图分析揭示了用于建模的基因（包括GMCL1、KRT8和OTUB1）的表达模式存在显著差异，KRT8和OTUB1基因在高危组中的表达水平显著高于低危组，而GMCL1表现出相反的变化（Figure
4 D-F）。

![](media/image4.png){width="5.768055555555556in"
height="5.089583333333334in"}

Figure4 泛素化和T细胞相关的关键基因预后风险模型的构建与验证。

（A-C）
KM分析显示，在训练集（A）、测试集（B）和验证集（C）3个数据集中，高危组患者的预后比低危组患者差。

（D-F）
生存分析显示，在训练集（A）、测试集（B）和验证集（C）3个数据集均显示高危组的死亡率较高。

**风险评分模型的有效性验证以及临床预测模型的构建与验证**

为了评估分类模型的性能，我们采用了ROC曲线进行分析。ROC曲线下的面积（AUC值）是衡量分类器性能的关键指标。在TCGA-train中，2,3,5
years,
AUC值分别为0.67、0.69和0.72；而在TCGA-test集中，AUC值分别为0.53、0.63和0.70。此外，GSE25066验证集的AUC值也表现出良好的性能，分别为0.62、0.63和0.59（Figure
5
A-C）。为了更深入地探究风险评分与临床特征之间的关系，我们进行了单因素和多因素COX预后分析。单因素COX分析显示，T分期、N分期和风险评分均具有显著的预后价值。此外，多因素COX回归分析进一步证实风险评分是一个有价值的独立预后因素（Figure
5
D-E）。考虑到将临床参数与风险评分相结合可能提高预后准确性，我们构建了一个列线图来预测患者2年、3年和5年的预后（Figure
5
F）。校准曲线验证表明该指标具有稳健的预测性能。进一步的ROC曲线分析显示AUC值高达0.719。此外，KM分析表明，列线图评分较高的患者预后较差（Figure
5 G-I）。

![](media/image5.png){width="5.768055555555556in"
height="8.622222222222222in"}

Figure 5 风险评分模型的疗效验证以及临床预测模型的构建和验证。

（A-C）

（D-E）单因素（F）和多因素（E）COX分析结果。

（F）通过整合风险评分和临床因素来构建列线图，以预测患者1、3和5年的生存率。

（G）校准曲线表明，该模型可以合理地预测患者的存活率。

（H）ROC曲线显示列线图评分的AUC值可达0.719。

（I）KM分析显示，列线图评分高的患者预后较差。

Chen C, Chen Z, Zhou Z, Ye H, Xiong S, Hu W, Xu Z, Ge C, Zhao C, Yu D,
Shen J (2024) T cell-related ubiquitination genes as prognostic
indicators in hepatocellular carcinoma. Frontiers in Immunology 15.
doi:10.3389/fimmu.2024.1424752
