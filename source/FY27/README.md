# source/FY27: where the FY2027 PDFs came from

**Last revised:** 2026-11-12 (the four FY2027 transparency resolutions, #246).

## Transparency resolutions (`transparency-resolutions/`)

Four resolutions adopted after the FY2027 budget, each the "Charts for Resolution" PDF of its
Legistar matter, plus the matter's resolution text ("Res. No.", a Word file). The charts PDFs
print no resolution text: each opens with "CHART #1: Local Initiatives - Fiscal 2027". The text
names the fiscal years the resolution changes and "Charts 1 through N", which the checks use
(`config/transparency/fy2027.toml`).

| File | Resolution | Adopted | Pages | Charts | sha256 |
|---|---|---|---:|---:|---|
| `Transparency-Reso-01-2026-07-16.pdf` | Res 0551-2026 | 2026-07-16 | 54 | 38 | `454393cb7276f228bcce5ba080c67573c5d0ffeba34b785d74f14bbfc00674ec` |
| `Transparency-Reso-01-2026-07-16-text.docx` | Res 0551-2026 (text) | | | | `71bb6f5efe3b271b046696a8d321c5d96b27300ce8a03b86e7d29a38112ab7ca` |
| `Transparency-Reso-02-2026-08-13.pdf` | Res 0595-2026 | 2026-08-13 | 48 | 40 | `5df6d3d6eb28e5e3837a25a2f13cab72f084e5cff55b6c16d6694556f4a1fd98` |
| `Transparency-Reso-02-2026-08-13-text.docx` | Res 0595-2026 (text) | | | | `fb367c484140ca1ea75c9abc001b3fb61ebb7d3da86e5e564260b1dca4780b7e` |
| `Transparency-Reso-03-2026-09-24.pdf` | Res 0652-2026 | 2026-09-24 | 89 | 49 | `668731690e142ac1215e69b1b9904bed9a2ef4afe1bf4201ad2392041e8df9bb` |
| `Transparency-Reso-03-2026-09-24-text.docx` | Res 0652-2026 (text) | | | | `e952c46b37ff80813c5e022ec5504d72b531a30b26726ad492ab0d0faae32358` |
| `Transparency-Reso-04-2026-10-22.pdf` | Res 0695-2026 | 2026-10-22 | 36 | 28 | `bd92d7699ff96872cb93ac2faad6a1b0a0b28a1aaf77af05c5690b31fd5fbfac` |
| `Transparency-Reso-04-2026-10-22-text.docx` | Res 0695-2026 (text) | | | | `419bf2579e1620705350519f566039cbbce69f90ef5c867342a3209798aae4c1` |

Every chart says which budget year it changes, and it is not always FY2027: these four also
change Fiscal 2026 (49 rows) and Fiscal 2025 (10 rows). Three charts print no year (review items).

### The download route

The Legistar **website** and the Legistar **Web API** number matters differently. The API's ids
(and `webapi.legistar.com`, which answered 403 without a token on 2026-08-14) do not open website
pages: a `LegislationDetail.aspx` URL built from them says "Invalid parameters!". What works:

1. Search the website, `https://legistar.council.nyc.gov/Legislation.aspx`, for the resolution
   (e.g. "551-2026").
2. Open the matter's page with the website's own id and GUID:
   `https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=<id>&GUID=<guid>`.
3. Its Attachments list links each file as
   `https://legistar.council.nyc.gov/View.ashx?M=F&ID=<file id>&GUID=<file guid>`.
   Plain `curl -L` with a browser User-Agent downloads them; no session or postback is needed.

| Resolution | Matter page (website) | Charts for Resolution | Res. No. (text) |
|---|---|---|---|
| Res 0551-2026 | `ID=8134167&GUID=1B43C13F-6DF6-4D49-82F7-A5AA8F7DCD1F` | `ID=15695414&GUID=BDC9DD90-BF61-47BC-9024-C64DC6257B53` | `ID=15693883&GUID=F8813FC8-01AE-4699-B850-EB94F4BAF1D9` |
| Res 0595-2026 | `ID=8166249&GUID=313C164B-F4F1-4D98-927D-B4B5702C3C64` | `ID=15762246&GUID=1FADC333-B4D8-45EB-A7EE-428AB1D9DD9C` | `ID=15762248&GUID=805B269C-8454-4B1F-9F27-04FEEEDF5750` |
| Res 0652-2026 | `ID=8219009&GUID=2A859448-CA37-40B2-848B-1D8CF1215BC0` | `ID=15932384&GUID=0D49435D-1213-41E1-9FAA-F8A779E21C20` | `ID=15932076&GUID=D196E0CE-02DC-4077-876B-64C1EB728222` |
| Res 0695-2026 | `ID=8286520&GUID=936A2CC8-6EC1-4D0C-A37D-38AD07AD987D` | `ID=16084529&GUID=A8894D44-AB9A-4A4B-9042-93C8933461F2` | `ID=16084528&GUID=918C89FB-60D1-4D0E-B3A1-C34CF73F6CC0` |

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
curl -sL -A "$UA" -o charts.pdf "https://legistar.council.nyc.gov/View.ashx?M=F&ID=15695414&GUID=BDC9DD90-BF61-47BC-9024-C64DC6257B53"
shasum -a 256 charts.pdf   # 454393cb…
```

**Checked 2026-11-12.** Noel uploaded the four charts PDFs; a fresh download by the route above
gave the same sha256 for all four. The four text files were downloaded the same day by the same
route. Each matter page shows "Status: Adopted", on the agenda of the date in the table.

**Next:** T2026-2764 is on the 2026-11-19 Finance agenda with no files yet. Add it here once
it is adopted and its charts are posted.

**FY2025 provenance** (#246 step 2) is still not on record: no note says how the 13 PDFs in
`source/FY25/transparency-resolutions/` were obtained. The route above should work for them too.
