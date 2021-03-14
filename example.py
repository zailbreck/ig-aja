from Instagram import Instagram

ig = Instagram({'username': '', 'password': '', 'proxy': None})
isAuth, message = ig.login() # ig.login(True) # print(ig.sharedData)
if isAuth:
    getMedia = ig.getMedia('https://www.instagram.com/p/CL_gnd4gfYX/')
    print(getMedia)
    userProfile = ig.userProfile('john_doe')
    print(userProfile)
    sharedData = ig._sharedData('/username/') # or '/'
    print(sharedData)
    posting = ig.posting('test.jpg', 'Caption', postType='feed') # postType='story'
    print(posting)
    search = ig.search('search keyword')
    print(search)
    comment = ig.comment('https://www.instagram.com/p/CL_gnd4gfYX/', 'this comment') # media url / id
    print(comment)
    like = ig.like('2521877765985269271') # media url / id
    print(like)
    follow = ig.follow('johnDoe') # username / userid
    print(follow)
    report = ig.report('username')
    print(report)
else:
    print(message)