#!/usr/bin/env python3
"""One-off helper: pull readable text from the TCP / TCA PDFs via pdftotext -layout.

Output is the concatenated page text, sliced around the relevant guide chapter for
hand-curation into data/*.json.

Usage:
    python3 tools/extract.py tcp502 [keyword]   # TCP 5.0.2 Upgrade Guide chapter
    python3 tools/extract.py tcp51  [keyword]   # TCP 5.1 Upgrade Guide chapter
    python3 tools/extract.py tca    [keyword]   # TCA 3.3.0.1 Kubernetes/Photon OS migration chapters
    python3 tools/extract.py tca34  [keyword]   # TCA 3.4 Kubernetes/Photon OS migration chapters
With no keyword, dumps the whole sliced region to stdout.
"""
import subprocess
import sys

TCP_502_PDF = "vmware-telco-cloud-platform-5-0-2.pdf"
TCP_51_PDF = "vmware-telco-cloud-platform-5-1.pdf"
TCA_PDF = "vmware-telco-cloud-automation-3-3-0-1.pdf"
TCA_34_PDF = "vmware-telco-cloud-automation-3-4.pdf"


def pdftotext(path):
    return subprocess.run(
        ["pdftotext", "-layout", path, "-"], capture_output=True, check=True
    ).stdout.decode("utf-8", errors="replace")


def slice_between(full, start_marker, end_marker, start_from=0):
    start = full.find(start_marker, start_from)
    if start < 0:
        return full
    end = full.find(end_marker, start)
    return full[start : end if end > 0 else None]


def tcp_guide_text(pdf):
    full = pdftotext(pdf)
    # Each per-release doc bundle has one real "Telco Cloud Platform Upgrade Guide" chapter, plus
    # several dotted table-of-contents entries earlier in the file. Anchor on the body's opening
    # paragraph, which is unique, then walk back to the chapter heading line above it.
    anchor = full.find("About the Telco Cloud Platform Upgrade Guide")
    while anchor >= 0 and "cloud-native platform powered by field-proven" not in full[anchor : anchor + 400]:
        anchor = full.find("About the Telco Cloud Platform Upgrade Guide", anchor + 1)
    start = full.rfind("Telco Cloud Platform Upgrade Guide", 0, anchor)
    end = full.find("Harbor for CNFs Deployment and Configuration Guide", start)
    return full[start : end if end > 0 else None]


def tca_k8s_photon_text(pdf, photon_range, k8s_range):
    # These guides run 700+ pages; hand-picked line ranges (via `pdftotext -layout | sed -n`)
    # for the two relevant chapters, verified by inspection, is far more reliable here than
    # searching for chapter titles that also appear in nested tables-of-contents.
    lines = pdftotext(pdf).split("\n")
    photon_os = "\n".join(lines[photon_range[0] : photon_range[1]])  # "Migrating from Photon OS 3 to Photon OS 5"
    k8s_hops = "\n".join(lines[k8s_range[0] : k8s_range[1]])  # "Upgrade Management/Workload Cluster Kubernetes Version"
    return photon_os + "\n\n---\n\n" + k8s_hops


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "tcp502"
    if which == "tcp502":
        full = tcp_guide_text(TCP_502_PDF)
    elif which == "tcp51":
        full = tcp_guide_text(TCP_51_PDF)
    elif which == "tca34":
        full = tca_k8s_photon_text(TCA_34_PDF, (34908, 35009), (12562, 12729))
    else:
        full = tca_k8s_photon_text(TCA_PDF, (34652, 34878), (12651, 12830))
    if len(sys.argv) > 2:
        kw = sys.argv[2]
        i = full.find(kw)
        print(full[i : i + 4000] if i >= 0 else f"'{kw}' not found")
    else:
        print(full)
