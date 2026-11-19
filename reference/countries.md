# PhD systems in Europe: working notes

Orientation only. Unless a source is given, figures are approximate, drawn from
general knowledge of the 2025-26 academic year, and change yearly with
collective agreements. Before a
number goes into a comparison or a decision, read it from the posting or the
official salary table and note the source. Tax and net pay depend on personal
circumstances.

| Country | Status | Typical length | Gross pay, rough | Entry rule to watch | Where posts appear |
|---|---|---|---|---|---|
| Netherlands | Employee (CAO universities, scale P) | 4 years | EUR 3,204 rising to 4,051 per month (read from a UvA advert on AcademicTransfer, Nov 2026), plus 8% holiday pay and 8.3% year-end bonus | Master's degree; 18-month go/no-go review | AcademicTransfer, university sites |
| Belgium (Flanders) | Bursary (tax-exempt) or employee | 4 years | about EUR 2,500-2,800 net per month | Master's with good grades; FWO fellowships have own calls | University sites, EURAXESS, FWO |
| Luxembourg | Employee (doctoral researcher) | up to 4 years | about EUR 41,000-43,000 per year | Master's; enrolment in a doctoral school | University of Luxembourg jobs, EURAXESS |
| Germany | Employee on TV-L E13, often 65-100% | 3-5 years, contract often shorter than the PhD | E13 full time about EUR 4,600-4,800 per month at entry; check the percentage | Recognition of foreign degrees by the faculty; German sometimes needed for teaching | academics.com, chair websites, DAAD, EURAXESS |
| Austria | Employee (university assistant prae-doc, usually 30 h/week) | 3-4 years | about EUR 2,700-2,800 per month for 30 h, paid 14 times | Master's; teaching duties common | University job portals, academics.com |
| Switzerland | Employee | 4 years | about CHF 50,000-58,000 per year, rising | Master's; high living costs | ETH/EPFL portals, academics.com |
| Denmark | Employee | 3 years | about DKK 30,000-33,000 per month plus pension | Two-year master's (120 ECTS) for the 3-year scheme | University sites, EURAXESS |
| Sweden | Employee (doktorand) | 4 years, up to 5 with 20% departmental duties | about SEK 30,000-36,000 per month on a ladder | 240 credits including 60 at advanced level; documents via Varbi; a "personal letter" | Varbi, university sites, EURAXESS |
| Norway | Employee (stipendiat, code 1017) | 3 years, or 4 with 25% duties | about NOK 550,000 per year | 120 ECTS master's, usually grade B or better; foreign degrees assessed; a project proposal is often required | Jobbnorge, EURAXESS |
| Finland | Employee or grant-funded | 4 years | about EUR 2,600-3,000 per month at entry | Study right in a doctoral programme is a separate step from the job | University sites, EURAXESS |
| France | Employee (contrat doctoral) | 3 years | about EUR 2,200-2,300 per month | Registration with a doctoral school | EURAXESS, lab sites, ADUM |
| Italy | Scholarship | 3 years | low; roughly EUR 1,200-1,400 net per month | National competition calls, mostly spring to summer | University calls, EURAXESS |
| Spain | Contract (FPI/FPU or project) | 4 years | roughly EUR 1,300-1,700 net per month | Call-specific rules | EURAXESS, university sites |
| United Kingdom | Student with a stipend | 3-4 years | UKRI minimum about GBP 20,800-21,800 per year, tax free | Many studentships cover home fees only; check international eligibility, visa and health surcharge costs | jobs.ac.uk, FindAPhD |
| Ireland | Student with a stipend | 4 years | about EUR 25,000 per year for funded awards | Fees and non-EU status | University sites, EURAXESS |

## MSCA Doctoral Networks (any country)

- **Mobility rule:** the candidate must not have resided or carried out their
  main activity (work, studies) in the host country for more than 12 months in
  the 36 months immediately before the recruitment date. Check the host
  country of each position against `countries_resided_over_12_months_in_last_36`
  in the profile, and re-check the dates as time passes: the window moves.
- Must not already hold a doctoral degree.
- Pay is a living allowance adjusted by a country coefficient plus a mobility
  allowance; usually above local PhD pay. Contract typically 36 months.
- Recruitment is per consortium with fixed start windows; adverts list several
  positions across countries, each with its own host.

## Things that differ and trip people up

- **Advertised post versus admission.** In NL, DK, SE, NO, LU the advert is the
  job. In DE, FI, IT, UK the funding, the supervisor and the enrolment can be
  three separate steps.
- **Proposal expected?** Norway, UK open calls and some Belgian, German and
  Swedish calls ask for a research proposal (2-5 pages). Dutch project PhDs
  usually do not; a short research statement at most.
- **Grade conversions.** Postings may ask for grade lists and a diploma
  supplement; Norwegian and Danish employers convert foreign grades. Do not
  convert a grade yourself: quote it on its own scale and flag the minimum as
  a `CHECK` unless an official conversion was read.
- **Language of the workplace.** Check teaching duties: an English-language
  project in Germany or Austria can still expect German for teaching.
- **Start date and permit.** Non-EU hires need a residence permit as a
  researcher or employee; the university usually sponsors it. Lead time is
  weeks to months. Depends on `eligibility.nationality` in the profile.
- **Contact person.** Most adverts name one. Writing before applying is normal
  in NL, the Nordics and Germany, and is the best way to resolve `CHECK` items.
  Some adverts forbid it; respect that.
- **Chair-based hiring.** In Germany, Austria and Switzerland many doctoral
  posts are never widely advertised: they sit on the chair's own website or
  go to people who wrote in. `prospect` and `outreach` matter most there.

## Judging whether a group is active

Look for recent papers at the main venues of the candidate's field (the
venues their own supervisors publish in are a good first list; ask during
setup and note them in `profile/profile.yml` under `research`), current
funded projects, and doctoral theses completed in the last five years.
Use this to judge the group, never as a claim about the candidate's record.

## Other boards worth a manual look

These block scripts (some show a bot check even in a browser), so phd-hunter
does not scan them: FindAPhD, DAAD PhDGermany, PhDportal, scholarshipdb,
Nature Careers, Times Higher Education jobs. University portals not yet
covered by a parser: see `docs/ADDING_A_BOARD.md`.
