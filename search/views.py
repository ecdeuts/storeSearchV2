from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from firebase import firebase

# Create your views here.
def sendFirebase(info, parent):
        #Connects to firebase using firebase library and sends info to parent directory
        fbase=firebase.FirebaseApplication('https://storesearch-4fd17.firebaseio.com', None)
        fbase.post(parent, info)
        return 0
def authorization():
        #authorizes script for use of Yelp API
	auth = Oauth1Authenticator(
		consumer_key = "qPax5LNdfH6cqZGxigS1Rg",
		consumer_secret = "h3Tqfk7nUvW2krMVBEGB5TmCtWA",
		token = "gCTsxxm_N98BczBYfpW8Z2Zx05HFwjP0",
		token_secret = "Kc2LMgNiUhFJN_-A6ltygKzD_c4"

		)	
	client = Client(auth)
	return client;
#set unused business attributes, business.eat24_url and bussiness.menu_provider to have deals information available on results.html
def addDeals(busiList):
        newURL = ""
        newTitle=""
        newBusiList=[]
        #itterates through deals list, and saves deal urls and deal titles
        for busi in busiList:
            for deal in busi.deals:
                newURL=newURL+deal.url+" "
                newTitle=newTitle+deal.title+" "
                #the eat24_url attribute and the menu_provider attribute are unsused, so set these attributes to be the deals url and deals title respectively
            busi.eat24_url=newURL
            #use the is_claimed attribute of businesses for Jinja logic in results .html decide wheter to print deals information
            busi.is_claimed=1
            busi.menu_provider=newTitle
            newBusiList.append(busi)
            newURL=""
            newTitle=""
        return newBusiList 
def addAddress(busiList):
        newString = ""
        newBusiList=[]
        for busi in busiList:
            for line in busi.location.display_address:
                #use new string to create string that contains the whole address
                newString+=line+" "
                #use the cross_streets attribute to contain the single string address
            busi.cross_streets=newString+" "
            newBusiList.append(busi)
            newString=""
        
        return newBusiList
def findParams(request):
        #read in values posted by home.html using .get
	terms=request.POST.get("term")
	location=request.POST.get("location")
	limit=request.POST.get("limit")
	#check that limit is within range 1-40
	if(limit<1):
                limit = 1
        elif(limit>40):
                limit=40
        deal=request.POST.get("deal")
        if(deal==None):
                deal=0
	sort=request.POST.get("sort")
	sort=convertSort(sort)
	radius=request.POST.get("distance")
        radius=convertDist(radius)
        #set parameters dictionary to the parameters found above
	params = {
	'location': location,
	'term': terms,
	'limit': limit,
	'sort': sort,
	'radius_filter': radius,
        'offset': 0,
        'deals_filter': deal
	}
	return params;
def makeListTags(busiList):
        #Make new list of catagories from business list
        newList = []
        a=0
        while(a<len(busiList)):
              newList.append(busiList[a].categories)
              a=a+1
        return newList
def deletePermClosed(busiList, params):
        #Check and deletes any permanetly closed businesses
        trueClosed=0
        deleteParams=params
        deleteParams['limit']=1
        offset=0
        length=0
        openList=[]
        for business in busiList:
                if(business.is_closed):
                        trueClosed=1;
        if(trueClosed):
                #itterate through many l searches, and then add into return list if not closed permanetly
                while(length<len(busiList)):
                        deleteParams['offset']=offset
                        search=client.search(**deleteParams)
                        if(1!=search[0].is_closed):
                                openList.append(search)
                                length=1+length
                        offset=offset+1
        else:
                openList=busiList
        return openList              
def convertDist(distance):
        #Changes string for radius decision from homepage to useable number
        if(distance=="5 mi or 8 km"):
           radius=8000
        elif(distance=="10 mi or 16 km"):
           radius=16000
        elif(distance=="15 mi or 24 km"):
           radius=24000
        elif(distance=="20 mi or 32 km"):
           radius=32000
        elif(distance=="25 mi or 40 km"):
           radius=40000
        else:
           radius=40000
        return radius
def convertSort(sort):
        #Converts string for sort decision to number used by business class
        if(sort=="By Best Match"):
           num=0
        elif(sort=="By Distance"):
           num=1
        elif(sort=="Highest Rated"):
           num=2
        else:
           num=0
        return num
def getTopTrends(trends):
        #Takes in dictionary and returns list of the 5 values that appear the most in the original dictionary
        fullList=trends.values()
        newList =[]
        #converts all strings to lowercase in list so that Abc is the same as abc when counting
        for string in fullList:
                string=string.lower()
                newList.append(string)
        fullList=newList
        noDoubl=list(set(fullList))
        #make list of the count of each item in noDoubl in fullList
        numList=[]
        for item in noDoubl:
                num=fullList.count(item)
                numList.append(num)
        #make dictionary of list of items with the amount of times it appeared in fullList
        matchDict=dict(zip(noDoubl, numList))
        topTrends=[]
        #Make ordered list with the items with the largest numbers of occurances first
        for key, value in sorted(matchDict.iteritems(),key=lambda (k,v): (v,k), reverse=True):
                topTrends.append(key)
        topCounter=0
        top5=[]
        #store top five items in list
        while(topCounter<5 and topCounter<len(topTrends)):
                top5.append(topTrends[topCounter])
                topCounter+=1
        return top5
def loadCatagory(busiList):
        #Stores catagories as a single string for each business in a list
        tag = ''
        catagoryList=[]
        for busi in busiList:
                for catagory in busi.categories:
                        tag +=catagory.name + ', '
                #change unused member .mobile_url into string list of catagories Jinja can parse
                tag=tag[:-2]
                busi.mobile_url=tag
                tag=''
        counter=0
        #Only stores first 10 businesses catagories or all if busiList's length is less than 10 to firebase, to limit processing time
        while(counter<10 and counter<len(busiList)):
                for category in busiList[counter].categories:
                        sendFirebase(category.name, '/Category')
                counter+=1
        return busiList
                        
        
def index(request):
        #first search page
        fbase=firebase.FirebaseApplication('https://storesearch-4fd17.firebaseio.com', None)
        #get top trends and top catagories to pass onto the html page home.html
        #top searched terms in term parameter
        topTrends=fbase.get('/Tags',None)
        #most common categories in results from all searches
        topCate=fbase.get('/Category',None)
        topList=getTopTrends(topTrends)
        topCateList=getTopTrends(topCate)
        #set trends and category info into dictionary so that Jinja can use it in the html page
        topDict={'trends': topList, 'category': topCateList}
        
        return render(request, 'search/home.html', topDict)
def results(request):
    #gets search terms, passes params to search results
        params=findParams(request)
        client=authorization()
        #search using Yelp library
        search=client.search(**params)
        #get business member from search resulsts
        cBusiness=search.businesses
        openBusi=deletePermClosed(cBusiness,params)
        openBusi=addAddress(openBusi)
        openBusi=loadCatagory(openBusi)
        #only send terms to firebase if there are results and if terms are entered by the user
        if(len(openBusi) and params['term']):
                sendFirebase(params['term'],'/Tags')
        #only get deals data if the user clicked "only search for deals"
        if(params['deals_filter']):
                openBusi=addDeals(openBusi)
        else:
                counter=0
                while(counter<len(openBusi)):
                        #set is_claimed to false so that the results page does not try to show deals data when there is none
                        openBusi[counter].is_claimed=0
                        counter +=1
        #send business information and tags information in results dictionary
        results={'place': openBusi,'tags': makeListTags(openBusi)}
        return render(request, 'search/results.html', results)
