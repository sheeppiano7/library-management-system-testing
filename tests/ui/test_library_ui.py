import uuid
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from practice_env import BASE, snapshot

def state(engine,bid):
    s=snapshot(engine)
    return next(b for b in s['books'] if b['book_id']==bid),[b for b in s['borrows'] if b['book_id']==bid]

@pytest.mark.parametrize('role,label',[('admin','管理员'),('operator','操作员'),('viewer','查看员')])
def test_UI01_role_login(page,role,label,engine):
    before=snapshot(engine)
    page.login(role)
    assert page.driver.current_url==BASE+'/'
    assert label in page.text and role in page.text
    assert before==snapshot(engine)

@pytest.mark.parametrize('role',['admin','operator','viewer'])
def test_UI02_wrong_password(page,role,engine):
    before=snapshot(engine)
    page.login(role,'wrong_test_password')
    assert page.driver.current_url.endswith('/login')
    assert '密码错误' in page.text
    assert before==snapshot(engine)

@pytest.mark.parametrize('path',['/books','/borrows'])
def test_UI03_anonymous_redirect(page,path,engine):
    before=snapshot(engine)
    page.open(path)
    assert page.driver.current_url.endswith('/login')
    assert before==snapshot(engine)

def test_UI04_book_create_and_search(page,engine):
    name='UI_BOOK_'+uuid.uuid4().hex[:10]
    page.login('admin').open('/books/add').fill('book_name',name).fill('author','合成作者').fill('category','自动化').fill('stock',1).submit()
    assert name in page.text
    rows=[b for b in snapshot(engine)['books'] if b['book_name']==name]
    assert len(rows)==1 and rows[0]['stock']==1
    page.open('/books/search?q='+name)
    assert name in page.text

def test_UI05_reader_create(page,engine):
    name='UI_READER_'+uuid.uuid4().hex[:10]
    phone='19'+str(uuid.uuid4().int%10**9).zfill(9)
    page.login('admin').open('/readers/add').fill('name',name).select('gender','其他').fill('phone',phone).submit()
    assert name in page.text
    assert len([r for r in snapshot(engine)['readers'] if r['name']==name and r['phone']==phone])==1

def test_UI06_duplicate_phone(page,engine,case_data):
    data=case_data(); before=snapshot(engine)
    page.login('operator').open('/readers/add').fill('name','UI_DUPLICATE').fill('phone',data['readers'][0]['phone']).submit()
    assert '手机号已存在' in page.text
    assert before==snapshot(engine)

def test_UI07_borrow_return_cycle(page,engine,case_data):
    data=case_data(); bid=data['bid']; rid=data['readers'][0]['reader_id']
    page.login('operator').borrow(bid,rid)
    book,loans=state(engine,bid)
    assert book['stock']==0 and len(loans)==1 and loans[0]['return_date'] is None
    assert data['name'] in page.text
    page.driver.find_element(By.CSS_SELECTOR,'a[href="/borrows/return/'+str(loans[0]['borrow_id'])+'"]').click()
    book,loans=state(engine,bid)
    assert book['stock']==1 and len(loans)==1 and loans[0]['return_date'] is not None
    assert '成功' in page.text

def test_UI08_duplicate_borrow(page,engine,case_data):
    data=case_data(2); bid=data['bid']; rid=data['readers'][0]['reader_id']
    page.login('operator').borrow(bid,rid)
    before=snapshot(engine)
    page.borrow(bid,rid)
    assert '已借阅此图书且未归还' in page.text
    assert before==snapshot(engine)

def test_UI09_stale_form_out_of_stock(page,engine,case_data):
    data=case_data(); bid=data['bid']; rid1,rid2=[r['reader_id'] for r in data['readers']]
    page.login('operator').open('/borrows/add').select('book_id',bid).select('reader_id',rid2)
    stale=page.driver.current_window_handle
    page.driver.switch_to.new_window('tab')
    page.borrow(bid,rid1)
    before=snapshot(engine)
    page.driver.close(); page.driver.switch_to.window(stale)
    page.submit()
    assert '库存不足' in page.text
    assert before==snapshot(engine)
    book,loans=state(engine,bid)
    assert book['stock']==0 and len(loans)==1

def test_UI10_zero_stock_not_selectable(page,engine,case_data):
    data=case_data(0); before=snapshot(engine)
    page.login('operator').open('/borrows/add')
    values=[o.get_attribute('value') for o in Select(page.driver.find_element(By.NAME,'book_id')).options]
    assert str(data['bid']) not in values
    assert before==snapshot(engine)

def test_UI11_viewer_buttons_hidden(page,engine):
    before=snapshot(engine)
    page.login('viewer')
    for path,selector in [('/books','a[href="/books/add"]'),('/readers','a[href="/readers/add"]'),('/borrows','a[href="/borrows/add"]')]:
        page.open(path)
        assert not page.driver.find_elements(By.CSS_SELECTOR,selector)
    assert before==snapshot(engine)

def test_UI12_viewer_direct_submit_denied(page,engine,case_data):
    data=case_data(); before=snapshot(engine)
    page.login('viewer').borrow(data['bid'],data['readers'][0]['reader_id'])
    assert '无操作权限' in page.text
    assert before==snapshot(engine)

def test_UI13_duplicate_return(page,engine,case_data,api):
    data=case_data(); bid=data['bid']
    page.login('operator').borrow(bid,data['readers'][0]['reader_id'])
    _,loans=state(engine,bid)
    path='/borrows/return/'+str(loans[0]['borrow_id'])
    page.open(path); before=snapshot(engine)
    page.open(path)
    assert '该图书已归还' in page.text
    assert before==snapshot(engine)

def test_UI14_logout_invalidates_session(page,engine):
    before=snapshot(engine)
    page.login('admin').open('/logout').open('/books')
    assert page.driver.current_url.endswith('/login')
    assert before==snapshot(engine)
