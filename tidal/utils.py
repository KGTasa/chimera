from db import cc

PRIVATE_API_URL = 'https://api.tidalhifi.com/v1/%s'
IMG_URL = 'https://resources.tidal.com/images/{}/' + cc.tidal_cover_size + '.jpg'
ARTIST_IMG_URL = 'http://images.osl.wimpmusic.com/im/im?w={width}&h={height}&{id_type}={id}'

# sm: 'https://resources.tidal.com/images/9a56f482-e9cf-46c3-bb21-82710e7854d4/160x160.jpg',
# md: 'https://resources.tidal.com/images/9a56f482-e9cf-46c3-bb21-82710e7854d4/320x320.jpg',
# lg: 'https://resources.tidal.com/images/9a56f482-e9cf-46c3-bb21-82710e7854d4/640x640.jpg',
# xl: 'https://resources.tidal.com/images/9a56f482-e9cf-46c3-bb21-82710e7854d4/1280x1280.jpg'



# proxies = {"https": "https://134.249.167.184:53281"}
proxies = {}