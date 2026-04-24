#!/usr/bin/python3
import anndata
from argparse import ArgumentParser
from jinja2 import Environment, PackageLoader, select_autoescape
import numpy
import pandas


DEFINITIONS = {
    "obs": {
        "cellID": "Index of obs table. Includes barcoding wells for each round (1_2_3), subpool, and experiment.",
        "lab_sample_id": "Human-readable sample name used in-house.",
        "sample": "IGVF tissue accession.",
        "plate": "Experiment ID, e.g. igvf_003.",
        "subpool": "Subpool ID, e.g. Subpool_2. Number corresponds to Illumina index ID from Parse Bio kit.",
        "SampleType": "Nuclei or Cells.",
        "Tissue": "Human-readable tissue name, e.g. Kidney.",
        "Sex": "Male or Female.",
        "Age": "Age in postnatal months (PNM) of the mouse, e.g. PNM_02.",
        "Genotype": "Mouse genotype/strain, e.g. B6J.",
        "leiden": "Numeric Leiden cluster starting from 0.",
        "leiden_R": "If necessary, Leiden clusters and any sub-clusters, e.g. 15_1.",
        "subpool_type": "Exome capture (EX) or no exome capture (NO).",
        "general_celltype": "Broadest level of cell type annotations, e.g. neuron.",
        "general_CL_ID": "EMBL CL database ID for general cell type annotation, e.g. CL:0000540.",
        "celltype": "Finest level of cell type annotation with a CL ID, e.g. Vip+ GABAergic cortical interneuron.",
        "CL_ID": "EMBL CL database ID for cell type annotation, CL:4023016",
        "subtype": "Finest level of cell type annotation that may not have a CL ID. Mostly matches celltype.",
        "Protocol": "Cell barcoding and library building protocol/kit, e.g. Parse_WT.",
        "Chemistry": "Protocol chemistry version, v2 or v3.",
        "bc": "24-nucleotide sequence corresponding to 3 8-nucleotide barcode rounds (3, 2, 1).",
        "bc1_sequence": "8-nucleotide sequence barcode for round 1.",
        "bc2_sequence": "8-nucleotide sequence barcode for round 2.",
        "bc3_sequence": "8-nucleotide sequence barcode for round 3.",
        "bc1_well": "Round 1 well.",
        "bc2_well": "Round 2 well.",
        "bc3_well": "Round 3 well.",
        "Row": "Sample barcoding plate (round 1) row.",
        "Column": "Sample barcoding plate (round 1) column.",
        "well_type": "Single or Multiplexed.",
        "Mouse_Tissue_ID": "Same as lab_sample_id.",
        "Multiplexed_sample1": "Sample 1 from multiplexed well (if applicable)",
        "Multiplexed_sample2": "Sample 2 from multiplexed well (if applicable)",
        "DOB": "Date of birth of the mouse in month/day/year format.",
        "Age_days": "Age of the mouse in days.",
        "Body_weight_g": "Body weight in grams of the mouse.",
        "Estrus_cycle": "Estimated estrus stage of the mouse, if applicable.",
        "Dissection_date": "Date the tissue was harvested in month/day/year format.",
        "Dissection_time": "Time in hours:minutes (24-hour time) the mouse was sacrificed.",
        "ZT": "Number of hours into the light cycle, from lights on (06:30, ZT0) to lights off (20:30, ZT14).",
        "Dissector": "Initials of technician who dissected the tissue.",
        "Tissue_weight_mg": "Tissue weight in milligrams.",
        "Total_extracted_million": "total number of nuclei extracted from the tissue",
        "Notes": "Notes taken during sample collection, experiment, or data processing.",
        "n_genes_by_counts": "The number of genes with at least 1 count.",
        "n_genes_by_counts_raw": "The number of genes with at least 1 count, calculated using raw counts.",
        "total_counts": "Total counts (UMIs), calculated using raw counts.",
        "total_counts_mt": "Total counts for mitochondrial genes, calculated using raw counts.",
        "total_counts_raw": "Total counts (UMIs), calculated using raw counts.",
        "total_counts_mt_raw": "Total counts for mitochondrial genes, calculated using raw counts.",
        "pct_counts_mt": "Percent of total counts in mitochondrial genes, calculated using raw counts.",
        "pct_counts_mt_raw": "Percent of total counts in mitochondrial genes, calculated using raw counts.",
        "n_genes_by_counts_cb": "The number of genes with at least 1 count, calculated using CellBender counts.",
        "total_counts_cb": "Total counts (UMIs), calculated using CellBender counts.",
        "total_counts_mt_cb": "Total counts for mitochondrial genes, calculated using CellBender counts.",
        "pct_counts_mt_cb": "Percent of total counts in mitochondrial genes, calculated using CellBender counts.",
        "doublet_score": "Scrublet doublet score, calculated using CellBender counts.",
        "predicted_doublet": "Scrublet predicted doublet (True or False).",
        "background_fraction": "Fraction of counts CellBender predicted to be background noise.",
        "cell_probability": "CellBender probability that the cell is real.",
        "cell_size": "CellBender size factor.",
        "droplet_efficiency": "CellBender statistic indicating transcript capture efficiency per cell.",
        "source": "internal path to the h5ad from before merging different experimental runs",
        "dataset": "a short internal name to describe what experiment phase this is",
        "sample_accession": "IGVF biosample accession, it may be a comma separated list",
        "donor_accession": "IGVF donor accession this sample was derived from",

        # klue genome names from the F1/Founder analysis
        "B6WSBF1J_klue_counts": "Estimated counts for B6WSBF1J genotype from klue analysis.",
        "B6NZOF1J_klue_counts": "Estimated counts for B6NZOF1J genotype from klue analysis.",
        "B6129S1F1J_klue_counts": "Estimated counts for B6129S1F1J genotype from klue analysis.",
        "B6CASTF1J_klue_counts": "Estimated counts for B6CASTF1J genotype from klue analysis.",
        "B6NODF1J_klue_counts": "Estimated counts for B6NODF1J genotype from klue analysis.",
        "B6AF1J_klue_counts": "Estimated counts for B6AF1J genotype from klue analysis.",
        "B6PWKF1J_klue_counts": "Estimated counts for B6WKF1J genotype from klue analysis.",

        # klue genome names from the original 8 cube experiment
        "B6J_klue_counts": "Estimated counts for B6J genotype from klue analysis.",
        "NODJ_klue_counts": "Estimated counts for NODJ genotype from klue analysis.",
        "AJ_klue_counts": "Estimated counts for AJ genotype from klue analysis.",
        "PWKJ_klue_counts": "Estimated counts for PWKJ genotype from klue analysis.",
        "129S1J_klue_counts": "Estimated counts for 129S1J genotype from klue analysis.",
        "CASTJ_klue_counts": "Estimated counts for CASTJ genotype from klue analysis.",
        "WSBJ_klue_counts": "Estimated counts for WSBJ genotype from klue analysis.",
        "NZOJ_klue_counts": "Estimated counts for NZOJ genotype from klue analysis.",
    },
    "var": {
        "gene_name": "Human-readable gene name, e.g. Xkr4.",
        "gene_id": "ENSEMBL gene ID, e.g. ENSMUSG00000051951.6.",
        "mt": "Boolean flag indicating if the gene is mitochondrial (e.g., starts with \"mt-\").",
        "highly_variable": "Boolean flag indicating if the gene is considered highly variable across cells.",
        "means": "Mean expression level of the gene across all cells.",
        "dispersions": "Raw dispersion (variance/mean) of the gene's expression across cells.",
        "dispersions_norm": "Normalized dispersion, adjusted for mean expression (used to find highly variable genes, HVGs).",
        "total_counts": "Total counts (UMIs), calculated using raw counts.",
        "mean_counts": "Mean expression over all cells.",
        "n_cells_by_counts": "Number of cells this expression is measured in",
        "pct_dropout_by_counts": "Percentage of cells this feature does not appear in",
        # terms found but didn't have any data attached to them
        "feature_type": "Unused",
        "genome": "Unused",

        # Guess from cellbender documentation
        "cellbender_analyzed": "Cellbender undocumented, probably was expression was adjusted",
        "ambient_expression": "Cellbender inferred profile of ambient RNA in the sample (normalized so it sums to one).",
    },
    "uns": {
        "hvg": "Method used to find HVGs, e.g. flavor: seurat.",
        "log1p": "Parameters used during log transformation.",
        "neighbors": "Information on the k-nearest neighbors graph: includes connectivities, distances, and other parameters.",
        "umap": "Parameters used to compute the UMAP embedding.",
        "leiden": "leiden parameters",

        # Diane's guesses
        "Genotype_colors": "list of #RGB colors used in plots of the Genotype obs field",
        "celltype_colors": "list of #RGB colors used in plots of the celltype obs field",
        "dendrogram_leiden_R": "object storing information needed to create endrogram plots of the leiden_R clustering",
        "dendrogram_subtype": "object storing information needed to create endrogram plots of the subtype clustering",
        "general_celltype_colors": "list of #RGB colors used in plots of the general_celltype obs field",
        "leiden_R_colors": "list of #RGB colors used in plots of the leiden_R obs field",
        "subpool_colors": "list of #RGB colors used in plots of the subpool obs field",
        "subpool_type_colors": "list of #RGB colors used in plots of the subpool_type obs field",
        "subtype_colors": "list of #RGB colors used in plots of the subtype obs field",

        # from cellbender documentation
        "barcode_indices_for_latents": "Undocumented cellbender field",
        "barcodes_analyzed": "Undocumented cellbender field",
        "barcodes_analyzed_inds": "Undocumented cellbender field",
        "cell_size_lognormal_std": "Undocumented cellbender field",
        "empty_droplet_size_lognormal_loc": "Undocumented cellbender field",
        "empty_droplet_size_lognormal_scale": "Undocumented cellbender field",
        "estimator": "name of cellbender estimator used",
        "features_analyzed_inds": "Undocumented cellbender field",
        "fraction_data_used_for_testing": "Not directly documented but probably --training-fraction argument",
        "swapping_fraction_dist_params": "Undocumented cellbender field",
        "target_false_positive_rate": "Not directly documented but probably --fpr false positive rate",

        "learning_curve_learning_rate_epoch": "Look similar to cellbender fields, but I couldn't find it",
        "learning_curve_learning_rate_value": "Look similar to cellbender fields, but I couldn't find it",

        "learning_curve_test_epoch":  "Undocumented cellbender field",
        "learning_curve_test_elbo":  "Undocumented cellbender field",
        "learning_curve_train_epoch": "Undocumented cellbender field",
        "learning_curve_train_elbo": "Undocumented cellbender field",
    },
    "obsm": {
        "X_pca": "Principal Component Analysis (PCA) coordinates for each cell.",
        "X_pca_harmony": "Harmony-adjusted PCA coordinates (corrected for technical batch effect between exome capture and non-exome capture libraries).",
        "X_umap": "UMAP embedding coordinates for each cell.",
        "gene_expression_encoding": "Latent gene expression embedding learned by CellBender.",
    },
    "layers": {
        "cellbender_counts": "CellBender-corrected cell-by-gene counts matrix.",
        "raw_counts": "Raw cell-by-gene counts matrix as calculated by Kallisto.",
    },
    "obsp": {
        "connectivities": "Graph of cell-to-cell connectivities used in clustering.",
        "distances": "Pairwise distances between cells used in clustering.",
    }
}


def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)

    report = generate_report(args.filename)

    if args.output:
        with open(args.output, "wt") as outstream:
            outstream.write(report)
    else:
        print(report)


def make_parser():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", help="target filename to write report to")
    parser.add_argument("filename", help="h5ad file to read")
    return parser


def generate_report(filename):
    used_terms = get_h5ad_attributes(filename)

    env = Environment(loader=PackageLoader("igvf_mice"), autoescape=select_autoescape())
    template = env.get_template("uci_lab_run_h5ad_file_specification.html")
    return template.render(**used_terms)


def get_h5ad_attributes(filename):
    used_terms = {}
    adata = anndata.read_h5ad(filename)
    table_names = ["obs", "var", "uns", "obsm", "layers", "obsp"]

    needs_definition = []
    used_terms = {}
    for table_name in table_names:
        table = getattr(adata, table_name)
        for key in table.keys():
            if key not in DEFINITIONS[table_name]:
                table_type = type(table[key])
                if isinstance(table[key], pandas.core.series.Series):
                    values = list(set(table[key]))[:5]
                elif isinstance(table[key], numpy.ndarray):
                    values = table[key].shape
                elif isinstance(table[key], numpy.float64):
                    values = table[key]
                elif isinstance(table[key], dict):
                    values = list(table.keys())[:5]
                else:
                    print(f"unrecognized table type {table_type}")
                    values = "Error"
                values = ""
                needs_definition.append((table_name, key, table_type, values))
                DEFINITIONS[table_name][key] = "ERROR: Undefined"

            used_terms.setdefault(table_name, {})[key] = DEFINITIONS[table_name][key]

    if len(needs_definition) > 0:
        print("table\tterm\tcoltype\tvalues")
        for table_name, term_name, coltype, values in needs_definition:
            print(f"{table_name}\t{term_name}\t{coltype}\t{values}")

    return used_terms


if __name__ == "__main__":
    main()
