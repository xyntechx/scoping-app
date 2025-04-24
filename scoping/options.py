class ScopingOptions:
    def __init__(
        self,
        enable_causal_links: bool = True,
        enable_merging: bool = True,
        enable_fact_based: bool = True,
        enable_forward_pass: bool = True,
        enable_loop: bool = True,
        write_output_file: bool = True
    ):
        self.enable_causal_links = enable_causal_links
        self.enable_merging = enable_merging
        self.enable_fact_based = enable_fact_based
        self.enable_forward_pass = enable_forward_pass
        self.enable_loop = enable_loop
        self.write_output_file = write_output_file
