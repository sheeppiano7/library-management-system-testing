# 逐条执行记录

逐条实际值及完整前后数据保存在引用JSON中；表内列出数据变化情况。未将历史失败覆盖为通过。

|项目/组|编号|场景|预期|实际核对|状态|证据|
|---|---|---|---|---|---|---|
|http_tests|ENV-LOGIN-admin|测试账号登录 admin|HTTP200首页显示角色；三库不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第1项|
|http_tests|ENV-LOGIN-operator|测试账号登录 operator|HTTP200首页显示角色；三库不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第2项|
|http_tests|ENV-LOGIN-viewer|测试账号登录 viewer|HTTP200首页显示角色；三库不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第3项|
|http_tests|ENV-SEED|测试图书、读者和三库种子核对|查询可见种子；三库均3图书2读者3账号0借阅0日志|前后数据不变|通过|../图书回归/runtime/http_tests.json，第4项|
|http_tests|BOOK-01|新增图书|新增QA_BOOK_A库存2；仅MySQL发生变化|mysql.books 3→4行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第5项|
|http_tests|BOOK-02|图书搜索|完整/部分书名命中；不存在词不出现QA_BOOK_A；数据不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第6项|
|http_tests|BOOK-03|编辑图书|作者和分类保存，库存仍2|mysql.books 4→4行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第7项|
|http_tests|BOOK-04|新增零库存图书|保存库存0，借阅下拉中无该图书|mysql.books 4→5行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第8项|
|http_tests|BOOK-05|负库存校验（拟定规则）|拒绝-1并给出提示；不新增记录|前后数据不变|通过|../图书回归/runtime/http_tests.json，第9项|
|http_tests|BOOK-06|书名长度边界100/101|100字保存，101字拒绝且非500，仅增加1行|mysql.books 5→6行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第10项|
|http_tests|READER-01|新增读者|新读者姓名手机号准确；仅增加1行|mysql.readers 2→3行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第11项|
|http_tests|READER-02|重复手机号|提示手机号已存在；三库数据不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第12项|
|http_tests|READER-03|读者空姓名和空格姓名|两次均明确拒绝，数据不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第13项|
|http_tests|READER-04|编辑并搜索读者|新姓名及电话准确，两个搜索都命中|mysql.readers 3→3行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第14项|
|http_tests|BORROW-01|正常借阅|未归还借阅增加1；库存2→1|mysql.books 6→6行（含字段变化）；mysql.borrows 0→1行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第15项|
|http_tests|BORROW-02|重复借阅|提示已借阅未归还；所有数据不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第16项|
|http_tests|BORROW-03|借走最后库存后继续借|仅新增1条，库存1→0；第二次提示库存不足|mysql.books 6→6行（含字段变化）；mysql.borrows 1→2行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第17项|
|http_tests|BORROW-ZERO|初始库存0强制借阅|提示库存不足且三库不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第18项|
|http_tests|BORROW-04|不存在图书|提示图书不存在，无写入|前后数据不变|通过|../图书回归/runtime/http_tests.json，第19项|
|http_tests|BORROW-05|不存在读者|有库存图书提交不存在读者，明确拒绝，无写入|前后数据不变|通过|../图书回归/runtime/http_tests.json，第20项|
|http_tests|DELETE-01|删除在借图书|保留图书借阅，页面显示无法删除|前后数据不变|通过|../图书回归/runtime/http_tests.json，第21项|
|http_tests|DELETE-02|删除有未归还记录读者|保留读者借阅，页面显示无法删除|前后数据不变|通过|../图书回归/runtime/http_tests.json，第22项|
|http_tests|RETURN-01|正常归还|记录写入归还时间，库存0→1|mysql.books 6→6行（含字段变化）；mysql.borrows 2→2行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第23项|
|http_tests|RETURN-02|重复归还|数据完全不变，页面提示已归还|前后数据不变|通过|../图书回归/runtime/http_tests.json，第24项|
|http_tests|RETURN-03|归还不存在记录|数据不变，页面提示借阅记录不存在|前后数据不变|通过|../图书回归/runtime/http_tests.json，第25项|
|http_tests|DELETE-03|删除无借阅关联的合成数据|成功删除刚新增的两条记录，其他行不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第26项|
|http_tests|PERM-01|查看员直连6种写接口|编辑/删除图书读者、借阅归还全部不改变三库数据|前后数据不变|通过|../图书回归/runtime/http_tests.json，第27项|
|http_tests|PERM-02|管理员与操作员各完成借还|新增2条已归还记录，库存恢复原值|mysql.books 6→6行（含字段变化）；mysql.borrows 2→4行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第28项|
|http_tests|PERM-03|两会话顺序交替不串用权限|管理员查看后，查看员新增被拒绝；重复3轮数据不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第29项|
|http_tests|STOCK-01|库存1，双会话同时借阅（一轮）|至多1条新借阅且库存=0，不超借|mysql.books 6→6行（含字段变化）；mysql.borrows 4→5行（含字段变化）|通过|../图书回归/runtime/http_tests.json，第30项|
|http_tests|STOCK-02|回查正常借还库存变化证据|正常借阅-1，首次归还+1，重复请求库存不变|前后数据不变|通过|../图书回归/runtime/http_tests.json，第31项|
|http_tests|OVERDUE-01|识别31天未归还但标志false的记录|逾期页面应包含QA_OVERDUE_ONLY|前后数据不变|通过|../图书回归/runtime/http_tests.json，第32项|
|http_tests|BOOK-NONINT|复现BUG-001非数字库存|明确校验提示，非500且无写入|前后数据不变|通过|../图书回归/runtime/http_tests.json，第33项|
|http_tests|BORROW-MISSING|复现BUG-002借阅缺参数|明确校验提示，非500且无写入|前后数据不变|通过|../图书回归/runtime/http_tests.json，第34项|
|service_tests|sqlserver-LOGIN-admin|测试账号认证 admin|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第1项|
|service_tests|sqlserver-LOGIN-operator|测试账号认证 operator|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第2项|
|service_tests|sqlserver-LOGIN-viewer|测试账号认证 viewer|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第3项|
|service_tests|sqlserver-QUERY|查询合成图书读者|原服务层返回3本种子图书、2名读者，无写入|前后数据不变|通过|../图书回归/runtime/service_tests.json，第4项|
|service_tests|sqlserver-BOOK-ADD|新增图书|成功保存库存2，仅当前测试库新增1行|sqlserver.books 3→4行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第5项|
|service_tests|sqlserver-READER-ADD|新增读者|姓名及手机号保存，仅当前库新增1行|sqlserver.readers 2→3行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第6项|
|service_tests|sqlserver-READER-DUP|重复手机号|返回手机号已存在，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第7项|
|service_tests|sqlserver-BOOK-EDIT|编辑图书|作者分类正确更新且库存仍2|sqlserver.books 4→4行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第8项|
|service_tests|sqlserver-READER-EDIT|编辑读者|姓名修改，手机号保持|sqlserver.readers 3→3行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第9项|
|service_tests|sqlserver-BORROW|正常借阅|新增未归还记录1条，库存2→1|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 0→1行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第10项|
|service_tests|sqlserver-DUP-BORROW|重复借阅|返回已借阅未归还，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第11项|
|service_tests|sqlserver-ZERO-STOCK|库存0借阅|返回库存不足，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第12项|
|service_tests|sqlserver-DELETE-BORROWED|删除在借图书及读者|两次拒绝且给出原因，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第13项|
|service_tests|sqlserver-VIEWER-WRITES|查看员直接调用8种写操作|全部返回无操作权限，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第14项|
|service_tests|sqlserver-RETURN|正常归还|归还时间写入、库存1→2|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 1→1行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第15项|
|service_tests|sqlserver-DUP-RETURN|重复归还|返回已归还，库存及三库数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第16项|
|service_tests|sqlserver-ADMIN-CYCLE|管理员完整借还|两步成功，新增1条已归还记录，库存不变|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 1→2行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第17项|
|service_tests|sqlserver-DELETE-UNLINKED|删除无关联合成图书读者|4步成功，删除后快照与准备前一致|前后数据不变|通过|../图书回归/runtime/service_tests.json，第18项|
|service_tests|postgresql-LOGIN-admin|测试账号认证 admin|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第19项|
|service_tests|postgresql-LOGIN-operator|测试账号认证 operator|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第20项|
|service_tests|postgresql-LOGIN-viewer|测试账号认证 viewer|密码验证成功、角色匹配、数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第21项|
|service_tests|postgresql-QUERY|查询合成图书读者|原服务层返回3本种子图书、2名读者，无写入|前后数据不变|通过|../图书回归/runtime/service_tests.json，第22项|
|service_tests|postgresql-BOOK-ADD|新增图书|成功保存库存2，仅当前测试库新增1行|postgresql.books 3→4行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第23项|
|service_tests|postgresql-READER-ADD|新增读者|姓名及手机号保存，仅当前库新增1行|postgresql.readers 2→3行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第24项|
|service_tests|postgresql-READER-DUP|重复手机号|返回手机号已存在，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第25项|
|service_tests|postgresql-BOOK-EDIT|编辑图书|作者分类正确更新且库存仍2|postgresql.books 4→4行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第26项|
|service_tests|postgresql-READER-EDIT|编辑读者|姓名修改，手机号保持|postgresql.readers 3→3行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第27项|
|service_tests|postgresql-BORROW|正常借阅|新增未归还记录1条，库存2→1|postgresql.books 4→4行（含字段变化）；postgresql.borrows 0→1行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第28项|
|service_tests|postgresql-DUP-BORROW|重复借阅|返回已借阅未归还，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第29项|
|service_tests|postgresql-ZERO-STOCK|库存0借阅|返回库存不足，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第30项|
|service_tests|postgresql-DELETE-BORROWED|删除在借图书及读者|两次拒绝且给出原因，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第31项|
|service_tests|postgresql-VIEWER-WRITES|查看员直接调用8种写操作|全部返回无操作权限，三库不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第32项|
|service_tests|postgresql-RETURN|正常归还|归还时间写入、库存1→2|postgresql.books 4→4行（含字段变化）；postgresql.borrows 1→1行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第33项|
|service_tests|postgresql-DUP-RETURN|重复归还|返回已归还，库存及三库数据不变|前后数据不变|通过|../图书回归/runtime/service_tests.json，第34项|
|service_tests|postgresql-ADMIN-CYCLE|管理员完整借还|两步成功，新增1条已归还记录，库存不变|postgresql.books 4→4行（含字段变化）；postgresql.borrows 1→2行（含字段变化）|通过|../图书回归/runtime/service_tests.json，第35项|
|service_tests|postgresql-DELETE-UNLINKED|删除无关联合成图书读者|4步成功，删除后快照与准备前一致|前后数据不变|通过|../图书回归/runtime/service_tests.json，第36项|
|extended|PARAM-STOCK-abc|新增库存非法输入 'abc'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第1项|
|extended|PARAM-STOCK-empty|新增库存非法输入 ''|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第2项|
|extended|PARAM-STOCK-1.5|新增库存非法输入 '1.5'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第3项|
|extended|PARAM-STOCK--1|新增库存非法输入 '-1'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第4项|
|extended|PARAM-STOCK-2147483648|新增库存非法输入 '2147483648'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第5项|
|extended|PARAM-BORROW-5|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第6项|
|extended|PARAM-BORROW-6|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第7项|
|extended|PARAM-BORROW-7|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第8项|
|extended|PARAM-BORROW-8|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第9项|
|extended|PARAM-BORROW-9|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第10项|
|extended|PARAM-EDIT|编辑库存非法输入|HTTP400，三库不变|前后数据不变；<Response [400]>|通过|../图书回归/runtime/extended.json，第11项|
|extended|POOL-90|同一服务连续90次列表请求|全部200，无超时，数据不变|前后数据不变；[200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200,|通过|../图书回归/runtime/extended.json，第12项|
|extended|AUTH-CONCURRENT|管理员查询与查看员写入同时进行12轮|查看员12次全部拒绝，数据不变|前后数据不变；[[(200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False)], [(200, Tr|通过|../图书回归/runtime/extended.json，第13项|
|extended|mysql-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 8→8行（含字段变化）；mysql.borrows 6→7行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 7)]|通过|../图书回归/runtime/extended.json，第14项|
|extended|mysql-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 9→9行（含字段变化）；mysql.borrows 7→8行（含字段变化）；[(True, '借阅成功', 8), (False, '图书库存不足')]|通过|../图书回归/runtime/extended.json，第15项|
|extended|mysql-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 10→10行（含字段变化）；mysql.borrows 8→9行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 9)]|通过|../图书回归/runtime/extended.json，第16项|
|extended|mysql-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|mysql.books 11→11行（含字段变化）；mysql.borrows 9→10行（含字段变化）；[(True, '借阅成功', 10), (False, '该读者已借阅此图书且未归还')]|通过|../图书回归/runtime/extended.json，第17项|
|extended|mysql-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|mysql.books 11→11行（含字段变化）；mysql.borrows 10→10行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|../图书回归/runtime/extended.json，第18项|
|extended|mysql-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[6, 11]|通过|../图书回归/runtime/extended.json，第19项|
|extended|sqlserver-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 5→5行（含字段变化）；sqlserver.borrows 2→3行（含字段变化）；[(True, '借阅成功', 3), (False, '图书库存不足')]|通过|../图书回归/runtime/extended.json，第20项|
|extended|sqlserver-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 6→6行（含字段变化）；sqlserver.borrows 3→4行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 4)]|通过|../图书回归/runtime/extended.json，第21项|
|extended|sqlserver-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 7→7行（含字段变化）；sqlserver.borrows 4→5行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 5)]|通过|../图书回归/runtime/extended.json，第22项|
|extended|sqlserver-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|sqlserver.books 8→8行（含字段变化）；sqlserver.borrows 5→6行（含字段变化）；[(True, '借阅成功', 6), (False, '该读者已借阅此图书且未归还')]|通过|../图书回归/runtime/extended.json，第23项|
|extended|sqlserver-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|sqlserver.books 8→8行（含字段变化）；sqlserver.borrows 6→6行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|../图书回归/runtime/extended.json，第24项|
|extended|sqlserver-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[7]|通过|../图书回归/runtime/extended.json，第25项|
|extended|postgresql-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 5→5行（含字段变化）；postgresql.borrows 2→3行（含字段变化）；[(True, '借阅成功', 3), (False, '图书库存不足')]|通过|../图书回归/runtime/extended.json，第26项|
|extended|postgresql-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 6→6行（含字段变化）；postgresql.borrows 3→4行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 4)]|通过|../图书回归/runtime/extended.json，第27项|
|extended|postgresql-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 7→7行（含字段变化）；postgresql.borrows 4→5行（含字段变化）；[(True, '借阅成功', 5), (False, '图书库存不足')]|通过|../图书回归/runtime/extended.json，第28项|
|extended|postgresql-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|postgresql.books 8→8行（含字段变化）；postgresql.borrows 5→6行（含字段变化）；[(True, '借阅成功', 6), (False, '该读者已借阅此图书且未归还')]|通过|../图书回归/runtime/extended.json，第29项|
|extended|postgresql-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|postgresql.books 8→8行（含字段变化）；postgresql.borrows 6→6行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|../图书回归/runtime/extended.json，第30项|
|extended|postgresql-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[7]|通过|../图书回归/runtime/extended.json，第31项|
