import json, os, sys, uuid, re
from datetime import datetime
from pathlib import Path
import pytest, requests
from selenium import webdriver

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from practice_env import BASE, target_engine, snapshot
from pages import LibraryPage

RUN = HERE / 'ui' / 'runs' / (datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4])
RUN.mkdir(parents=True)
os.environ['SE_CACHE_PATH'] = str(HERE/'runtime'/'selenium')

@pytest.fixture(scope='session')
def engine():
    e=target_engine('mysql')
    yield e
    e.dispose()

@pytest.fixture
def api():
    s=requests.Session(); s.trust_env=False
    password=os.environ.get('BOOK_OPERATOR_PASSWORD')
    if not password:
        pytest.skip('Set BOOK_OPERATOR_PASSWORD for UI tests')
    r=s.post(BASE+'/login',data={'username':'operator','password':password},timeout=15)
    assert r.status_code==200 and '操作员' in r.text
    yield s
    s.close()

@pytest.fixture
def case_data(api,engine):
    token='UI_'+uuid.uuid4().hex[:10]
    def create(stock=1):
        name=token+'_'+str(stock)
        r=api.post(BASE+'/books/add',data={'book_name':name,'author':'合成作者','category':'自动化测试','stock':stock},timeout=15)
        assert r.status_code==200
        readers=[]
        for i in range(2):
            rn=name+'_R'+str(i)
            phone='19'+str(uuid.uuid4().int%10**9).zfill(9)
            r=api.post(BASE+'/readers/add',data={'name':rn,'gender':'其他','phone':phone},timeout=15)
            assert r.status_code==200
            readers.append(rn)
        state=snapshot(engine)
        return {'name':name,'bid':next(b['book_id'] for b in state['books'] if b['book_name']==name),
                'readers':[next(r for r in state['readers'] if r['name']==rn) for rn in readers]}
    yield create
    # Retain synthetic rows, return only this test's outstanding loans via the business endpoint.
    s=snapshot(engine); ids={b['book_id'] for b in s['books'] if b['book_name'].startswith(token)}
    returned=[]
    for b in s['borrows']:
        if b['book_id'] in ids and b['return_date'] is None:
            r=api.get(BASE+'/borrows/return/'+str(b['borrow_id']),timeout=15)
            returned.append({'borrow_id':b['borrow_id'],'http':r.status_code})
    (RUN/(token+'_cleanup.json')).write_text(json.dumps({'returns':returned,'state':snapshot(engine)},ensure_ascii=False,indent=2),encoding='utf-8')

@pytest.fixture
def page(request,engine):
    options=webdriver.EdgeOptions()
    if os.environ.get('HEADED')!='1': options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1100')
    options.add_argument('--no-proxy-server')
    d=webdriver.Edge(options=options)
    request.node.driver=d
    request.node.case_start=datetime.now().isoformat()
    request.node.before=snapshot(engine)
    yield LibraryPage(d,BASE)
    d.quit()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    result=yield
    report=result.get_result()
    if report.when!='call': return
    driver=getattr(item,'driver',None)
    safe=re.sub(r'[^A-Za-z0-9_-]', '_', item.name)
    data={'id':item.name,'status':report.outcome,'started':getattr(item,'case_start',None),
          'ended':datetime.now().isoformat(),'duration':report.duration,'error':str(report.longrepr) if report.failed else None,
          'before':getattr(item,'before',None)}
    if 'engine' in item.funcargs: data['after']=snapshot(item.funcargs['engine'])
    if driver:
        driver.save_screenshot(str(RUN/(safe+'.png')))
        data.update(url=driver.current_url,browser=driver.capabilities.get('browserVersion'),actual_text=driver.find_element('tag name','body').text)
        (RUN/(safe+'.html')).write_text(driver.page_source,encoding='utf-8')
    (RUN/(safe+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def pytest_sessionfinish(session,exitstatus):
    (RUN/'run.json').write_text(json.dumps({'exitstatus':exitstatus,'finished':datetime.now().isoformat(),'results_directory':str(RUN)},ensure_ascii=False,indent=2),encoding='utf-8')
    print('\nEvidence:',RUN)
