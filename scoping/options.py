from dataclasses import dataclass


@dataclass
class ScopingOptions:
    enable_causal_links: bool = True
    enable_merging: bool = True
    enable_fact_based: bool = True
    enable_forward_pass: bool = True
    enable_loop: bool = True
    write_output_file: bool = True
