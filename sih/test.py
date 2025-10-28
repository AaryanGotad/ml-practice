import requests

BASE = "http://127.0.0.1:5000/" # the base url to refer to

data = [{"name": "hello", "views": 300, "likes": 22},
        {"name": "The Interstellar Experience", "views": 1000, "likes": 100},
        {"name": "Turning 18 & New Year 2025", "views": 500, "likes": 57}]

# sending a get request to the base url and 'heeloworld' in addition to it
# basically the url will now become "(BASE)/helloworld"
# and then printing the reponse got from that url, in json format to prevent it being printing as an request object

# get_response = requests.get(BASE + "helloworld/aaryan")
# print(f"GET request sent to {BASE}/helloworld/aaryan")
# print(get_response.json())
# input()

# put_response = requests.put(BASE + "video/1", {"name": "hello", "views": 300, "likes": 10})
# print(f"PUT request sent to {BASE}/video/(video_id) and name, views, likes as input arguments. This will assign the following arguments to videos set having index = video_id")
# print(put_response.json())
# input()

for i in range(len(data)):
    response = requests.put(BASE + "video/" + str(i), data[i])
    print(f"Response status: {response.status_code}")
    if response.status_code == 201:  # Created successfully
        print(f"Video {i} created:", response.json())
    else:
        print(f"Error creating video {i}: {response.json()}")

input()
patch_response = requests.patch(BASE + "video/2", {"likes":99})
print(patch_response.json())

get_response = requests.get(BASE + "video/2")  # Try getting the first video
print(f"\nGET request sent to {BASE}/video/0 to get details of the first video")
if get_response.status_code == 200:
    print("Video details:", get_response.json())
else:
    print(f"Error getting video: {get_response.text}")
# input()

# delete_response = requests.delete(BASE + "video/0")
# print(delete_response)
# post_response = requests.post(BASE + "helloworld")
# print(post_response.json())