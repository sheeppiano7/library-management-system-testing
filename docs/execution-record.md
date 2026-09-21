# 逐条执行记录

逐条实际值及完整前后数据保存在引用JSON中；表内列出变化行数与执行时间。未将历史失败覆盖为通过。

|项目/组|编号|场景|预期|实际核对|状态|执行时间|证据|
|---|---|---|---|---|---|---|---|
|http_tests|ENV-LOGIN-admin|测试账号登录 admin|HTTP200首页显示角色；三库不变|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第1项|
|http_tests|ENV-LOGIN-operator|测试账号登录 operator|HTTP200首页显示角色；三库不变|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第2项|
|http_tests|ENV-LOGIN-viewer|测试账号登录 viewer|HTTP200首页显示角色；三库不变|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第3项|
|http_tests|ENV-SEED|测试图书、读者和三库种子核对|查询可见种子；三库均3图书2读者3账号0借阅0日志|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第4项|
|http_tests|BOOK-01|新增图书|新增QA_BOOK_A库存2；仅MySQL发生变化|mysql.books 3→4行（含字段变化）|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第5项|
|http_tests|BOOK-02|图书搜索|完整/部分书名命中；不存在词不出现QA_BOOK_A；数据不变|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第6项|
|http_tests|BOOK-03|编辑图书|作者和分类保存，库存仍2|mysql.books 4→4行（含字段变化）|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第7项|
|http_tests|BOOK-04|新增零库存图书|保存库存0，借阅下拉中无该图书|mysql.books 4→5行（含字段变化）|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第8项|
|http_tests|BOOK-05|负库存校验（拟定规则）|拒绝-1并给出提示；不新增记录|前后数据不变|通过|2026-09-16T22:01:04|../图书回归/runtime/http_tests.json，第9项|
|http_tests|BOOK-06|书名长度边界100/101|100字保存，101字拒绝且非500，仅增加1行|mysql.books 5→6行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第10项|
|http_tests|READER-01|新增读者|新读者姓名手机号准确；仅增加1行|mysql.readers 2→3行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第11项|
|http_tests|READER-02|重复手机号|提示手机号已存在；三库数据不变|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第12项|
|http_tests|READER-03|读者空姓名和空格姓名|两次均明确拒绝，数据不变|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第13项|
|http_tests|READER-04|编辑并搜索读者|新姓名及电话准确，两个搜索都命中|mysql.readers 3→3行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第14项|
|http_tests|BORROW-01|正常借阅|未归还借阅增加1；库存2→1|mysql.books 6→6行（含字段变化）；mysql.borrows 0→1行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第15项|
|http_tests|BORROW-02|重复借阅|提示已借阅未归还；所有数据不变|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第16项|
|http_tests|BORROW-03|借走最后库存后继续借|仅新增1条，库存1→0；第二次提示库存不足|mysql.books 6→6行（含字段变化）；mysql.borrows 1→2行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第17项|
|http_tests|BORROW-ZERO|初始库存0强制借阅|提示库存不足且三库不变|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第18项|
|http_tests|BORROW-04|不存在图书|提示图书不存在，无写入|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第19项|
|http_tests|BORROW-05|不存在读者|有库存图书提交不存在读者，明确拒绝，无写入|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第20项|
|http_tests|DELETE-01|删除在借图书|保留图书借阅，页面显示无法删除|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第21项|
|http_tests|DELETE-02|删除有未归还记录读者|保留读者借阅，页面显示无法删除|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第22项|
|http_tests|RETURN-01|正常归还|记录写入归还时间，库存0→1|mysql.books 6→6行（含字段变化）；mysql.borrows 2→2行（含字段变化）|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第23项|
|http_tests|RETURN-02|重复归还|数据完全不变，页面提示已归还|前后数据不变|通过|2026-09-16T22:01:05|../图书回归/runtime/http_tests.json，第24项|
|http_tests|RETURN-03|归还不存在记录|数据不变，页面提示借阅记录不存在|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第25项|
|http_tests|DELETE-03|删除无借阅关联的合成数据|成功删除刚新增的两条记录，其他行不变|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第26项|
|http_tests|PERM-01|查看员直连6种写接口|编辑/删除图书读者、借阅归还全部不改变三库数据|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第27项|
|http_tests|PERM-02|管理员与操作员各完成借还|新增2条已归还记录，库存恢复原值|mysql.books 6→6行（含字段变化）；mysql.borrows 2→4行（含字段变化）|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第28项|
|http_tests|PERM-03|两会话顺序交替不串用权限|管理员查看后，查看员新增被拒绝；重复3轮数据不变|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第29项|
|http_tests|STOCK-01|库存1，双会话同时借阅（一轮）|至多1条新借阅且库存=0，不超借|mysql.books 6→6行（含字段变化）；mysql.borrows 4→5行（含字段变化）|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第30项|
|http_tests|STOCK-02|回查正常借还库存变化证据|正常借阅-1，首次归还+1，重复请求库存不变|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第31项|
|http_tests|OVERDUE-01|识别31天未归还但标志false的记录|逾期页面应包含QA_OVERDUE_ONLY|前后数据不变|通过|2026-09-16T22:01:06|../图书回归/runtime/http_tests.json，第32项|
|http_tests|BOOK-NONINT|复现BUG-001非数字库存|明确校验提示，非500且无写入|前后数据不变|通过|2026-09-16T22:01:07|../图书回归/runtime/http_tests.json，第33项|
|http_tests|BORROW-MISSING|复现BUG-002借阅缺参数|明确校验提示，非500且无写入|前后数据不变|通过|2026-09-16T22:01:07|../图书回归/runtime/http_tests.json，第34项|
|service_tests|sqlserver-LOGIN-admin|测试账号认证 admin|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:07|../图书回归/runtime/service_tests.json，第1项|
|service_tests|sqlserver-LOGIN-operator|测试账号认证 operator|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第2项|
|service_tests|sqlserver-LOGIN-viewer|测试账号认证 viewer|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第3项|
|service_tests|sqlserver-QUERY|查询合成图书读者|原服务层返回3本种子图书、2名读者，无写入|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第4项|
|service_tests|sqlserver-BOOK-ADD|新增图书|成功保存库存2，仅当前测试库新增1行|sqlserver.books 3→4行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第5项|
|service_tests|sqlserver-READER-ADD|新增读者|姓名及手机号保存，仅当前库新增1行|sqlserver.readers 2→3行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第6项|
|service_tests|sqlserver-READER-DUP|重复手机号|返回手机号已存在，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第7项|
|service_tests|sqlserver-BOOK-EDIT|编辑图书|作者分类正确更新且库存仍2|sqlserver.books 4→4行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第8项|
|service_tests|sqlserver-READER-EDIT|编辑读者|姓名修改，手机号保持|sqlserver.readers 3→3行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第9项|
|service_tests|sqlserver-BORROW|正常借阅|新增未归还记录1条，库存2→1|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 0→1行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第10项|
|service_tests|sqlserver-DUP-BORROW|重复借阅|返回已借阅未归还，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第11项|
|service_tests|sqlserver-ZERO-STOCK|库存0借阅|返回库存不足，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第12项|
|service_tests|sqlserver-DELETE-BORROWED|删除在借图书及读者|两次拒绝且给出原因，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第13项|
|service_tests|sqlserver-VIEWER-WRITES|查看员直接调用8种写操作|全部返回无操作权限，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第14项|
|service_tests|sqlserver-RETURN|正常归还|归还时间写入、库存1→2|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 1→1行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第15项|
|service_tests|sqlserver-DUP-RETURN|重复归还|返回已归还，库存及三库数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第16项|
|service_tests|sqlserver-ADMIN-CYCLE|管理员完整借还|两步成功，新增1条已归还记录，库存不变|sqlserver.books 4→4行（含字段变化）；sqlserver.borrows 1→2行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第17项|
|service_tests|sqlserver-DELETE-UNLINKED|删除无关联合成图书读者|4步成功，删除后快照与准备前一致|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第18项|
|service_tests|postgresql-LOGIN-admin|测试账号认证 admin|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第19项|
|service_tests|postgresql-LOGIN-operator|测试账号认证 operator|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第20项|
|service_tests|postgresql-LOGIN-viewer|测试账号认证 viewer|密码验证成功、角色匹配、数据不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第21项|
|service_tests|postgresql-QUERY|查询合成图书读者|原服务层返回3本种子图书、2名读者，无写入|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第22项|
|service_tests|postgresql-BOOK-ADD|新增图书|成功保存库存2，仅当前测试库新增1行|postgresql.books 3→4行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第23项|
|service_tests|postgresql-READER-ADD|新增读者|姓名及手机号保存，仅当前库新增1行|postgresql.readers 2→3行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第24项|
|service_tests|postgresql-READER-DUP|重复手机号|返回手机号已存在，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第25项|
|service_tests|postgresql-BOOK-EDIT|编辑图书|作者分类正确更新且库存仍2|postgresql.books 4→4行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第26项|
|service_tests|postgresql-READER-EDIT|编辑读者|姓名修改，手机号保持|postgresql.readers 3→3行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第27项|
|service_tests|postgresql-BORROW|正常借阅|新增未归还记录1条，库存2→1|postgresql.books 4→4行（含字段变化）；postgresql.borrows 0→1行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第28项|
|service_tests|postgresql-DUP-BORROW|重复借阅|返回已借阅未归还，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第29项|
|service_tests|postgresql-ZERO-STOCK|库存0借阅|返回库存不足，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第30项|
|service_tests|postgresql-DELETE-BORROWED|删除在借图书及读者|两次拒绝且给出原因，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第31项|
|service_tests|postgresql-VIEWER-WRITES|查看员直接调用8种写操作|全部返回无操作权限，三库不变|前后数据不变|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第32项|
|service_tests|postgresql-RETURN|正常归还|归还时间写入、库存1→2|postgresql.books 4→4行（含字段变化）；postgresql.borrows 1→1行（含字段变化）|通过|2026-09-16T22:01:08|../图书回归/runtime/service_tests.json，第33项|
|service_tests|postgresql-DUP-RETURN|重复归还|返回已归还，库存及三库数据不变|前后数据不变|通过|2026-09-16T22:01:09|../图书回归/runtime/service_tests.json，第34项|
|service_tests|postgresql-ADMIN-CYCLE|管理员完整借还|两步成功，新增1条已归还记录，库存不变|postgresql.books 4→4行（含字段变化）；postgresql.borrows 1→2行（含字段变化）|通过|2026-09-16T22:01:09|../图书回归/runtime/service_tests.json，第35项|
|service_tests|postgresql-DELETE-UNLINKED|删除无关联合成图书读者|4步成功，删除后快照与准备前一致|前后数据不变|通过|2026-09-16T22:01:09|../图书回归/runtime/service_tests.json，第36项|
|extended|PARAM-STOCK-abc|新增库存非法输入 'abc'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.125353|../图书回归/runtime/extended.json，第1项|
|extended|PARAM-STOCK-empty|新增库存非法输入 ''|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.152721|../图书回归/runtime/extended.json，第2项|
|extended|PARAM-STOCK-1.5|新增库存非法输入 '1.5'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.187212|../图书回归/runtime/extended.json，第3项|
|extended|PARAM-STOCK--1|新增库存非法输入 '-1'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.203849|../图书回归/runtime/extended.json，第4项|
|extended|PARAM-STOCK-2147483648|新增库存非法输入 '2147483648'|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.221479|../图书回归/runtime/extended.json，第5项|
|extended|PARAM-BORROW-5|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.240600|../图书回归/runtime/extended.json，第6项|
|extended|PARAM-BORROW-6|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.260869|../图书回归/runtime/extended.json，第7项|
|extended|PARAM-BORROW-7|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.292333|../图书回归/runtime/extended.json，第8项|
|extended|PARAM-BORROW-8|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.320763|../图书回归/runtime/extended.json，第9项|
|extended|PARAM-BORROW-9|借阅缺参或非法编号|HTTP400，三库无变化|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.349069|../图书回归/runtime/extended.json，第10项|
|extended|PARAM-EDIT|编辑库存非法输入|HTTP400，三库不变|前后数据不变；<Response [400]>|通过|2026-09-16T22:01:10.380411|../图书回归/runtime/extended.json，第11项|
|extended|POOL-90|同一服务连续90次列表请求|全部200，无超时，数据不变|前后数据不变；[200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200,|通过|2026-09-16T22:01:10.419190|../图书回归/runtime/extended.json，第12项|
|extended|AUTH-CONCURRENT|管理员查询与查看员写入同时进行12轮|查看员12次全部拒绝，数据不变|前后数据不变；[[(200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False), (200, False)], [(200, Tr|通过|2026-09-16T22:01:12.523899|../图书回归/runtime/extended.json，第13项|
|extended|mysql-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 8→8行（含字段变化）；mysql.borrows 6→7行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 7)]|通过|2026-09-16T22:01:12.936271|../图书回归/runtime/extended.json，第14项|
|extended|mysql-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 9→9行（含字段变化）；mysql.borrows 7→8行（含字段变化）；[(True, '借阅成功', 8), (False, '图书库存不足')]|通过|2026-09-16T22:01:13.004205|../图书回归/runtime/extended.json，第15项|
|extended|mysql-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|mysql.books 10→10行（含字段变化）；mysql.borrows 8→9行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 9)]|通过|2026-09-16T22:01:13.063602|../图书回归/runtime/extended.json，第16项|
|extended|mysql-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|mysql.books 11→11行（含字段变化）；mysql.borrows 9→10行（含字段变化）；[(True, '借阅成功', 10), (False, '该读者已借阅此图书且未归还')]|通过|2026-09-16T22:01:13.126468|../图书回归/runtime/extended.json，第17项|
|extended|mysql-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|mysql.books 11→11行（含字段变化）；mysql.borrows 10→10行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|2026-09-16T22:01:13.179836|../图书回归/runtime/extended.json，第18项|
|extended|mysql-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[6, 11]|通过|2026-09-16T22:01:13.298798|../图书回归/runtime/extended.json，第19项|
|extended|sqlserver-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 5→5行（含字段变化）；sqlserver.borrows 2→3行（含字段变化）；[(True, '借阅成功', 3), (False, '图书库存不足')]|通过|2026-09-16T22:01:13.433064|../图书回归/runtime/extended.json，第20项|
|extended|sqlserver-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 6→6行（含字段变化）；sqlserver.borrows 3→4行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 4)]|通过|2026-09-16T22:01:13.512981|../图书回归/runtime/extended.json，第21项|
|extended|sqlserver-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|sqlserver.books 7→7行（含字段变化）；sqlserver.borrows 4→5行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 5)]|通过|2026-09-16T22:01:13.562749|../图书回归/runtime/extended.json，第22项|
|extended|sqlserver-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|sqlserver.books 8→8行（含字段变化）；sqlserver.borrows 5→6行（含字段变化）；[(True, '借阅成功', 6), (False, '该读者已借阅此图书且未归还')]|通过|2026-09-16T22:01:13.610964|../图书回归/runtime/extended.json，第23项|
|extended|sqlserver-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|sqlserver.books 8→8行（含字段变化）；sqlserver.borrows 6→6行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|2026-09-16T22:01:13.663829|../图书回归/runtime/extended.json，第24项|
|extended|sqlserver-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[7]|通过|2026-09-16T22:01:13.756067|../图书回归/runtime/extended.json，第25项|
|extended|postgresql-RACE-1|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 5→5行（含字段变化）；postgresql.borrows 2→3行（含字段变化）；[(True, '借阅成功', 3), (False, '图书库存不足')]|通过|2026-09-16T22:01:13.878629|../图书回归/runtime/extended.json，第26项|
|extended|postgresql-RACE-2|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 6→6行（含字段变化）；postgresql.borrows 3→4行（含字段变化）；[(False, '图书库存不足'), (True, '借阅成功', 4)]|通过|2026-09-16T22:01:14.011515|../图书回归/runtime/extended.json，第27项|
|extended|postgresql-RACE-3|库存1双线程借阅|一成功一拒绝，库存0，仅一条借阅|postgresql.books 7→7行（含字段变化）；postgresql.borrows 4→5行（含字段变化）；[(True, '借阅成功', 5), (False, '图书库存不足')]|通过|2026-09-16T22:01:14.064453|../图书回归/runtime/extended.json，第28项|
|extended|postgresql-DUP-CONCURRENT|同一读者并发重复借阅|仅一条借阅，库存2变1|postgresql.books 8→8行（含字段变化）；postgresql.borrows 5→6行（含字段变化）；[(True, '借阅成功', 6), (False, '该读者已借阅此图书且未归还')]|通过|2026-09-16T22:01:14.121763|../图书回归/runtime/extended.json，第29项|
|extended|postgresql-RETURN-CONCURRENT|同一借阅并发归还|一次成功，库存只恢复1，归还时间保存|postgresql.books 8→8行（含字段变化）；postgresql.borrows 6→6行（含字段变化）；[(False, '该图书已归还'), (True, '归还成功')]|通过|2026-09-16T22:01:14.184540|../图书回归/runtime/extended.json，第30项|
|extended|postgresql-OVERDUE|按实际日期筛选未归还逾期记录|含31天未归还，排除29天与已归还；读操作无写入|前后数据不变；[7]|通过|2026-09-16T22:01:14.283749|../图书回归/runtime/extended.json，第31项|
|takeaway_final|REG-001|注册角色QA_SHOP|增加1条账号，账号和角色数值准确|userinof 0→1行（含字段变化）|通过|2026-09-16T22:27:22|../外卖回归/run_222721/results.json cases第1项|
|takeaway_final|REG-002|注册角色QA_CUSTOMER|增加1条账号，账号和角色数值准确|userinof 1→2行（含字段变化）|通过|2026-09-16T22:27:22|../外卖回归/run_222721/results.json cases第2项|
|takeaway_final|REG-003|注册角色QA_RIDER|增加1条账号，账号和角色数值准确|userinof 2→3行（含字段变化）|通过|2026-09-16T22:27:23|../外卖回归/run_222721/results.json cases第3项|
|takeaway_final|REG-004|注册角色QA_ADMIN|增加1条账号，账号和角色数值准确|userinof 3→4行（含字段变化）|通过|2026-09-16T22:27:23|../外卖回归/run_222721/results.json cases第4项|
|takeaway_final|REG-005|重复账号|拒绝重复账号，数据不变|前后数据不变|通过|2026-09-16T22:27:23|../外卖回归/run_222721/results.json cases第5项|
|takeaway_final|REG-006|空用户名|拒绝空用户名|userinof 4→5行（含字段变化）|失败|2026-09-16T22:27:24|../外卖回归/run_222721/results.json cases第6项|
|takeaway_final|REG-007|单引号用户名|合法姓名可以保存|userinof 5→6行（含字段变化）|通过|2026-09-16T22:27:24|../外卖回归/run_222721/results.json cases第7项|
|takeaway_final|REG-008|非法角色255|拒绝非法角色|userinof 6→7行（含字段变化）|失败|2026-09-16T22:27:24|../外卖回归/run_222721/results.json cases第8项|
|takeaway_final|DATA-001|手机号从数据库到UDP响应一致性|返回原始11位手机号13900000001|前后数据不变；{'returned_phones': [1015098113, 1015098113, 1015098113, 1015098113, 1015098113, 1015098113, 1015098113]}|失败|2026-09-16T22:27:25|../外卖回归/run_222721/results.json cases第9项|
|takeaway_final|AUTH-002|未登录读取账号列表的密码字段|未认证请求不返回可用明文密码|前后数据不变；{'synthetic_password_exposed': True, 'user_count': 7}|失败|2026-09-16T22:27:25|../外卖回归/run_222721/results.json cases第10项|
|takeaway_final|MENU-001|新增菜品价格25.5|新增菜品，金额准确|custommenu 0→1行（含字段变化）|通过|2026-09-16T22:27:25|../外卖回归/run_222721/results.json cases第11项|
|takeaway_final|MENU-002|菜品编辑价格|同商户菜单替换，价格26.75|custommenu 1→1行（含字段变化）|通过|2026-09-16T22:27:25|../外卖回归/run_222721/results.json cases第12项|
|takeaway_final|MENU-003|第二商户菜单不覆盖第一商户|保留第一商户菜品，新增第二商户菜品|custommenu 1→2行（含字段变化）|通过|2026-09-16T22:27:25|../外卖回归/run_222721/results.json cases第13项|
|takeaway_final|MENU-004|重复提交同商户菜单|不产生重复菜品|custommenu 2→2行（含字段变化）|通过|2026-09-16T22:27:26|../外卖回归/run_222721/results.json cases第14项|
|takeaway_final|MENU-005|负菜品价格|负价格拒绝且保留旧菜单|custommenu 2→2行（含字段变化）|失败|2026-09-16T22:27:26|../外卖回归/run_222721/results.json cases第15项|
|takeaway_final|MENU-006|单引号菜品名更新|合法名称可以更新，异常也不得删除原菜单|custommenu 2→2行（含字段变化）|通过|2026-09-16T22:27:26|../外卖回归/run_222721/results.json cases第16项|
|takeaway_final|MENU-007|恢复合成菜单|恢复合成菜单用于后续订单测试|custommenu 2→2行（含字段变化）|通过|2026-09-16T22:27:27|../外卖回归/run_222721/results.json cases第17项|
|takeaway_final|MENU-008|同批重复菜品UUID|同一UUID只保存1条菜品|custommenu 2→3行（含字段变化）|失败|2026-09-16T22:27:27|../外卖回归/run_222721/results.json cases第18项|
|takeaway_final|MENU-009|混合商户报文|混合批次不得制造重复菜品|custommenu 3→3行（含字段变化）|失败|2026-09-16T22:27:27|../外卖回归/run_222721/results.json cases第19项|
|takeaway_final|ORD-001|合法订单写入与金额字段保存|存储1条订单，金额25.5|menuorder 0→1行（含字段变化）|通过|2026-09-16T22:27:28|../外卖回归/run_222721/results.json cases第20项|
|takeaway_final|ORD-002|订单正常状态更新 1|仍1条订单，状态更新为1|menuorder 1→1行（含字段变化）|通过|2026-09-16T22:27:28|../外卖回归/run_222721/results.json cases第21项|
|takeaway_final|ORD-003|订单正常状态更新 2|仍1条订单，状态更新为2|menuorder 1→1行（含字段变化）|通过|2026-09-16T22:27:29|../外卖回归/run_222721/results.json cases第22项|
|takeaway_final|ORD-004|订单正常状态更新 3|仍1条订单，状态更新为3|menuorder 1→1行（含字段变化）|通过|2026-09-16T22:27:29|../外卖回归/run_222721/results.json cases第23项|
|takeaway_final|ORD-005|单条报文重复提交|相同订单重复发送不新增第二条|menuorder 1→1行（含字段变化）|通过|2026-09-16T22:27:29|../外卖回归/run_222721/results.json cases第24项|
|takeaway_final|ORD-006|已完成订单回退待接单|已完成订单不得回退到新建状态|menuorder 1→1行（含字段变化）|失败|2026-09-16T22:27:30|../外卖回归/run_222721/results.json cases第25项|
|takeaway_final|ORD-007|非法枚举状态255|拒绝非法状态，数据不变化|menuorder 1→1行（含字段变化）|失败|2026-09-16T22:27:30|../外卖回归/run_222721/results.json cases第26项|
|takeaway_final|ORD-008|负订单金额|拒绝负金额，数据不变化|menuorder 1→2行（含字段变化）|失败|2026-09-16T22:27:30|../外卖回归/run_222721/results.json cases第27项|
|takeaway_final|ORD-009|同批两条重复订单|同一业务订单只能保存1条|menuorder 2→4行（含字段变化）|失败|2026-09-16T22:27:31|../外卖回归/run_222721/results.json cases第28项|
|takeaway_final|ORD-010|合法名称包含单引号|合法菜品名称保留单引号并正常保存|menuorder 4→5行（含字段变化）|通过|2026-09-16T22:27:31|../外卖回归/run_222721/results.json cases第29项|
|takeaway_final|ORD-011|已存在订单更新为含单引号名称|更新失败时也不得丢失原订单|menuorder 5→5行（含字段变化）|通过|2026-09-16T22:27:31|../外卖回归/run_222721/results.json cases第30项|
|takeaway_final|NET-001|短报文|忽略短报文，数据库不变|前后数据不变|通过|2026-09-16T22:27:32|../外卖回归/run_222721/results.json cases第31项|
|takeaway_final|NET-002|未知消息类型|忽略未知报文，数据库不变|前后数据不变|通过|2026-09-16T22:27:32|../外卖回归/run_222721/results.json cases第32项|
|takeaway_final|NET-003|订单报文长度不足|拒绝不完整报文|前后数据不变|通过|2026-09-16T22:27:32|../外卖回归/run_222721/results.json cases第33项|
|takeaway_final|NET-004|订单报文多出1字节|拒绝长度不符报文|前后数据不变|通过|2026-09-16T22:27:33|../外卖回归/run_222721/results.json cases第34项|
|takeaway_final|ORD-012|六位整数金额的小数精度|123456.78金额精确保存|menuorder 5→6行（含字段变化）|通过|2026-09-16T22:27:33|../外卖回归/run_222721/results.json cases第35项|
|takeaway_final|AUTH-001|未配置客户端未登录提交订单|未认证来源不能创建订单|menuorder 6→7行（含字段变化）|失败|2026-09-16T22:27:34|../外卖回归/run_222721/results.json cases第36项|
|takeaway_final|REG-009|中文用户名原样保存|中文姓名完整保存|userinof 7→8行（含字段变化）|通过|2026-09-16T22:27:34|../外卖回归/run_222721/results.json cases第37项|
|takeaway_final|ORD-013|中文菜品名称与小数金额|中文名称和0.01金额正确保存|menuorder 7→8行（含字段变化）|通过|2026-09-16T22:27:34|../外卖回归/run_222721/results.json cases第38项|
|takeaway_final|ORD-014|空订单UUID|拒绝空业务标识|menuorder 8→9行（含字段变化）|失败|2026-09-16T22:27:35|../外卖回归/run_222721/results.json cases第39项|
|takeaway_final|ORD-015|空读者对应的客户标识|订单必须关联客户，拒绝空客户标识|menuorder 9→10行（含字段变化）|失败|2026-09-16T22:27:35|../外卖回归/run_222721/results.json cases第40项|
|takeaway_final|ORD-016|空菜品名称|拒绝缺少菜品内容的订单|menuorder 10→11行（含字段变化）|失败|2026-09-16T22:27:35|../外卖回归/run_222721/results.json cases第41项|
|takeaway_final|ORD-017|常规金额9999.99|9999.99原样保存|menuorder 11→12行（含字段变化）|通过|2026-09-16T22:27:36|../外卖回归/run_222721/results.json cases第42项|
|takeaway_final|NET-005|零字节数据报|忽略空数据报，状态不变|前后数据不变|通过|2026-09-16T22:27:36|../外卖回归/run_222721/results.json cases第43项|
|takeaway_final|NET-006|仅订单消息头|拒绝只有消息头的报文|前后数据不变|通过|2026-09-16T22:27:36|../外卖回归/run_222721/results.json cases第44项|
|takeaway_final|NET-007|空订单批次|空批次不删除或新增订单|前后数据不变|通过|2026-09-16T22:27:37|../外卖回归/run_222721/results.json cases第45项|
|takeaway_final|NET-008|空菜品批次|空批次无法指定商户，不得删除其他菜单|前后数据不变|通过|2026-09-16T22:27:37|../外卖回归/run_222721/results.json cases第46项|
|takeaway_final|DATA-002|角色账号与中文姓名返回一致性|返回角色10至13，账号和中文用户名与数据库一致|前后数据不变|通过|2026-09-16T22:27:37|../外卖回归/run_222721/results.json cases第47项|
|takeaway_final|FIX-MENU-PRICE|菜品金额123456.78|菜品价格精确保留小数|custommenu 3→3行（含字段变化）|通过|2026-09-16T22:27:37|../外卖回归/run_222721/results.json cases第48项|
|takeaway_final|FIX-MENU-QUOTE|单引号菜品完整保存|菜品名称原样保存|custommenu 3→3行（含字段变化）|通过|2026-09-16T22:27:38|../外卖回归/run_222721/results.json cases第49项|
|takeaway_final|FIX-ORDER-SEED|准备事务回滚订单|创建专用合成订单|menuorder 12→13行（含字段变化）|通过|2026-09-16T22:27:38|../外卖回归/run_222721/results.json cases第50项|
|takeaway_final|FIX-ORDER-ROLLBACK|订单删除后插入失败回滚|强制插入失败，完整保留原订单|前后数据不变|通过|2026-09-16T22:27:38|../外卖回归/run_222721/results.json cases第51项|
|takeaway_final|FIX-MENU-ROLLBACK|整批菜品删除后插入失败回滚|强制插入失败，完整保留原菜单|前后数据不变|通过|2026-09-16T22:27:39|../外卖回归/run_222721/results.json cases第52项|
|takeaway_final|FIX-RECOVERY|失败事务后继续更新订单|失败后服务仍可用，单引号和金额准确|menuorder 13→13行（含字段变化）|通过|2026-09-16T22:27:39|../外卖回归/run_222721/results.json cases第53项|
|takeaway_final|ENV-001|独立服务重启后的数据持久性|重启后表数据不丢失且用户列表可查询|前后数据不变|通过|2026-09-16T22:27:40|../外卖回归/run_222721/results.json cases第54项|