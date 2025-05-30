from pdfreport.one_pdf_to_md import pdf_to_md
from pdfreport.two_clean_markdown import clean_markdown
from pdfreport.three_md_to_summary import md_to_summary
from parameters import friday_date

def auto_weekly_reports():
    print('start auto weekly reports')
    pdf_to_md(friday_date)
    print('pdf to md done')
    clean_markdown(friday_date)
    print('clean markdown done')
    md_to_summary(friday_date)
    print('md to summary done')