[![Build Status](https://travis-ci.com/estherh5/api.crystalprism.io.svg?branch=master)](https://travis-ci.com/estherh5/api.crystalprism.io)
[![codecov](https://codecov.io/gh/estherh5/api.crystalprism.io/branch/master/graph/badge.svg)](https://codecov.io/gh/estherh5/api.crystalprism.io)

# api.crystalprism.io
I started programming in January 2017 and am learning Python for back-end server development. api.crystalprism.io is the API for my website, [Crystal Prism](https://crystalprism.io). The API allows for the storage and retrieval of game scores, user-created drawings and thought posts, as well as user accounts. For user security, I implemented a JWT authentication flow from scratch that includes generating and verifying secure user tokens.

## Setup
1. Clone this repository on your server.
2. Install requirements by running `pip install -r requirements.txt`.
3. Create a PostgreSQL database to store user information, as well as a user that has all privileges on your database.
4. Create a Cloudflare R2 bucket (e.g., `crystalprism`) and enable its public development URL (or attach a custom domain) so photos and drawings can be served publicly. Create an R2 API token with Object Read & Write access to the bucket. Upload both thumbnails and full-size homepage photos to the bucket's `photos/` folder; CanvaShare drawings are stored under `canvashare/`.
    * Full-size photos should be named as numbers (e.g., "1.png"), and thumbnails must be named the same plus the suffix "-thumb" (e.g., "1-thumb.png").
    * For best display on the front-end, full-size photos should be 6 x 8 inches in size, and thumbnails should be 240 x 300 px.
5. Set the following environment variables for the API:
    * `FLASK_APP` for the Flask application name for your server (`server.py`)
    * `SECRET_KEY` for the salt used to generate the signature portion of the JWT for user authentication (set this as a secret key that only you know; it is imperative to keep this private for user account protection)
    * `ENV_TYPE` for the environment status (set this to `Dev` for testing or `Prod` for live)
    * `R2_ACCOUNT_ID` for your Cloudflare account ID
    * `R2_ACCESS_KEY_ID` and `R2_SECRET_ACCESS_KEY` for the R2 API token's S3-compatible credentials
    * `R2_BUCKET` for the name of your R2 bucket (e.g., `crystalprism`)
    * `R2_PUBLIC_BASE` for the bucket's public URL, without a trailing slash (e.g., `https://pub-<id>.r2.dev`)
    * `DB_CONNECTION` for the [dsn parameter string](http://initd.org/psycopg/docs/module.html) to connect to your database via psycopg2 (e.g., `dbname=<database_name> user=<database_user> password=<database_user_password> host=<database_host>`)
    * `DB_NAME` for the name of your database
    * `DB_USER` for the user who has all privileges on your database
6. Initialize the database by running `python management.py init_db`, and load initial data (webpage owner user whose posts appear on the homepage Ideas page, admin user, initial homepage Ideas page post written by webpage owner, how-to Thought Writer posts written by admin, sample drawing created by admin) by running `python management.py load_data`.
7. Start the server by running `flask run` (if you are making changes while the server is running, enter `flask run --reload` instead for instant updates).


## API Status
To check if the API is online, a client can send a request to the following endpoint.

**GET** /api/ping
* Retrieve a success message if the server is online. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
Success
```


## CanvaShare API
#### March 2017 - Present
[CanvaShare](https://canvashare.crystalprism.io/index.html) is a community drawing gallery that lets users create drawings and post them to a public gallery. Each user's drawings get saved to a Cloudflare R2 bucket, and drawing attributes (title, URL, view count, drawing likes) get saved in the Crystal Prism database "drawing" and "drawing_like" tables:
<p align="center"><img title="CanvaShare Database Tables" src ="images/canvashare-tables.png" /></p>

Note that the following environment variables must be set:
  - "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY" and "R2_BUCKET" must be set to your Cloudflare R2 account, API token credentials and bucket name
  - "R2_PUBLIC_BASE" must be set to the bucket's public URL (e.g., 'https://pub-<id>.r2.dev')

\
**POST** /api/canvashare/drawing
* Post a drawing by sending the jsonified drawing data URI in base64 format and drawing title in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "drawing": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAZ...",
    "title": "Welcome"
}
```

\
**GET** /api/canvashare/drawing/[drawing_id]
* Retrieve an artist's drawing attributes by specifying the drawing id in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "created": "2017-10-05T00:00:21.412Z",
    "drawing_id": 1,
    "like_count": 2,
    "likers": [
      {
        "drawing_like_id": 2,
        "username": "esther"
      },
      {
        "drawing_like_id": 1,
        "username": "admin"
      }
    ],
    "title": "Welcome",
    "url": "https://pub-<id>.r2.dev/canvashare/1.png",
    "username": "admin",
    "views": 10
}
```

\
**PATCH** /api/canvashare/drawing/[drawing_id]
* Update a drawing's view count by specifying the drawing id in the request URL. No bearer token is needed in the request Authorization header.

\
**DELETE** /api/canvashare/drawing/[drawing_id]
* Delete a drawing by specifying the drawing id in the request URL. Note that there must be a verified bearer token for the artist in the request Authorization header.

\
**GET** /api/canvashare/drawings?start=[request_start]&end=[request_end]
* Retrieve all users' drawing attributes in order of newest to oldest. Optionally specify the number of drawings via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
        "created": "2017-10-08T14:39:10.403Z",
        "drawing_id": 4,
        "like_count": 0,
        "likers": [],
        "title": "Dreams",
        "url": "https://pub-<id>.r2.dev/canvashare/4.png",
        "username": "esther",
        "views": 4
    },
    {
        "created": "2017-10-07T10:23:19.232Z",
        "drawing_id": 3,
        "like_count": 1,
        "likers": [
          {
            "drawing_like_id": 5,
            "username": "esther"
          }
        ],
        "title": "Good Night",
        "url": "https://pub-<id>.r2.dev/canvashare/3.png",
        "username": "esther",
        "views": 5
    },
    {
        "created": "2017-10-06T20:34:20.490Z",
        "drawing_id": 2,
        "like_count": 1,
        "likers": [
          {
            "drawing_like_id": 8,
            "username": "esther"
          }
        ],
        "title": "Strings",
        "url": "https://pub-<id>.r2.dev/canvashare/2.png",
        "username": "esther",
        "views": 1
    },
    {
        "created": "2017-10-05T00:00:21.412Z",
        "drawing_id": 1,
        "like_count": 2,
        "likers": [
          {
            "drawing_like_id": 2,
            "username": "esther"
          },
          {
            "drawing_like_id": 1,
            "username": "admin"
          }
        ],
        "title": "Welcome",
        "url": "https://pub-<id>.r2.dev/canvashare/1.png",
        "username": "admin",
        "views": 10
    }
]
```

\
**GET** /api/canvashare/drawings/[artist_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's drawing attributes in order of newest to oldest by specifying the artist's username in the request URL. Optionally specify the number of drawings via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
        "created": "2017-10-08T14:39:10.403Z",
        "drawing_id": 4,
        "like_count": 0,
        "likers": [],
        "title": "Dreams",
        "url": "https://pub-<id>.r2.dev/canvashare/4.png",
        "username": "esther",
        "views": 4
    },
    {
        "created": "2017-10-07T10:23:19.232Z",
        "drawing_id": 3,
        "like_count": 1,
        "likers": [
          {
            "drawing_like_id": 5,
            "username": "esther"
          }          
        ],
        "title": "Good Night",
        "url": "https://pub-<id>.r2.dev/canvashare/3.png",
        "username": "esther",
        "views": 5
    },
    {
        "created": "2017-10-06T20:34:20.490Z",
        "drawing_id": 2,
        "like_count": 1,
        "likers": [
          {
            "drawing_like_id": 8,
            "username": "esther"
          }
        ],
        "title": "Strings",
        "url": "https://pub-<id>.r2.dev/canvashare/2.png",
        "username": "esther",
        "views": 1
    }
]
```

\
**POST** /api/canvashare/drawing-like
* Post a drawing like by sending the jsonified drawing id in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "drawing_id": 1
}
```

\
**GET** /api/canvashare/drawing-like/[drawing_like_id]
* Retrieve a drawing like by specifying the drawing like in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "created": "2017-10-06T23:39:11.101Z",
    "drawing_id": 1,
    "drawing_like_id": 1,
    "username": "admin"
}
```

\
**DELETE** /api/canvashare/drawing-like/[drawing_like_id]
* Delete a drawing like by specifying the drawing like id in the request URL. Note that there must be a verified bearer token for the liker in the request Authorization header.

\
**GET** /api/canvashare/drawing-likes/drawing/[drawing_id]?start=[request_start]&end=[request_end]
* Retrieve all users' likes for a drawing in order of newest to oldest by specifying the drawing id in the request URL. Optionally specify the number of likes via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example request body:
```javascript
{
    "drawing_id": 1
}
```
* Example response body:
```javascript
[
    {
      "created": "2017-10-07T21:32:20.028Z",
      "drawing_id": 1,
      "drawing_like_id": 2,
      "username": "esther"
    },
    {
      "created": "2017-10-06T23:39:11.101Z",
      "drawing_id": 1,
      "drawing_like_id": 1,
      "username": "admin"
    }
]
```

\
**GET** /api/canvashare/drawing-likes/user/[liker_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's likes in order of newest to oldest by specifying the liker's username in the request URL. Optionally specify the number of liked drawings via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "artist_name": "esther",
      "created": "2017-10-07T11:01:02.209Z",
      "drawing_id": 3,
      "drawing_like_id": 5,
      "like_count": 1,
      "likers": [
        {
          "drawing_like_id": 5,
          "username": "esther"
        }          
      ],
      "title": "Good Night",
      "url": "https://pub-<id>.r2.dev/canvashare/3.png",
      "username": "esther",
      "views": 5
    },
    {
      "artist_name": "esther",
      "created": "2017-10-07T10:21:20.320Z",
      "drawing_id": 2,
      "like_count": 1,
      "likers": [
        {
          "drawing_like_id": 8,
          "username": "esther"
        }
      ],
      "drawing_like_id": 8,
      "title": "Strings",
      "url": "https://pub-<id>.r2.dev/canvashare/2.png",
      "username": "esther",
      "views": 1
    },
    {
      "artist_name": "admin",
      "created": "2017-10-07T21:32:20.028Z",
      "drawing_id": 1,
      "drawing_like_id": 2,
      "like_count": 2,
      "likers": [
        {
          "drawing_like_id": 2,
          "username": "esther"
        },
        {
          "drawing_like_id": 1,
          "username": "admin"
        }
      ],
      "title": "Welcome",
      "url": "https://pub-<id>.r2.dev/canvashare/1.png",
      "username": "esther",
      "views": 10
    }
]
```


## Rhythm of Life API
#### July 2017 - Present
[Rhythm of Life](https://rhythm-of-life.crystalprism.io/index.html) is an educational take on the classic game Snake, involving moving a heart to avoid stressors and seek relievers to maintain a healthy blood pressure. Rhythm of Life information is stored in the "rhythm_score" database table:
<p align="center"><img title="Rhythm of Life Database Table" src ="images/rhythm-table.png" /></p>

\
**POST** /api/rhythm-of-life/score
* Post a score by sending the jsonified score in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "score": 91
}
```

\
**GET** /api/rhythm-of-life/score/[score_id]
* Retrieve a score by sending the score id in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "created": "2017-10-27T04:00:51.122Z",
    "score": 91,
    "score_id": 12,
    "username": "esther"
},
```

\
**DELETE** /api/rhythm-of-life/score/[score_id]
* Delete a score by sending the score id in the request URL. Note that there must be a verified bearer token for the player in the request Authorization header.

\
**GET** /api/rhythm-of-life/scores?start=[request_start]&end=[request_end]
* Retrieve all users' game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "created": "2017-10-27T04:00:51.122Z",
      "score": 91,
      "score_id": 12,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:54:50.401Z",
      "score": 23,
      "score_id": 10,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:53:31.133Z",
      "score": 17,
      "score_id": 9,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:55:04.103Z",
      "score": 9,
      "score_id": 11,
      "username": "esther"
    },
    {
      "created": "2017-10-24T00:19:29.485Z",
      "score": 9,
      "score_id": 6,
      "username": "admin"
    }
]
```

\
**GET** /api/rhythm-of-life/scores/[player_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "created": "2017-10-27T04:00:51.122Z",
      "score": 91,
      "score_id": 12,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:54:50.401Z",
      "score": 23,
      "score_id": 10,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:53:31.133Z",
      "score": 17,
      "score_id": 9,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:55:04.103Z",
      "score": 9,
      "score_id": 11,
      "username": "esther"
    },
    {
      "created": "2017-10-27T03:50:14.098Z",
      "score": 8,
      "score_id": 8,
      "username": "esther"
    }
]
```


## Thought Writer API
#### August 2017 - Present
[Thought Writer](https://thought-writer.crystalprism.io/index.html) is a community post board for users to post ideas for others to read and comment on. Thought Writer information is stored in the "post" and "comment" database tables:
<p align="center"><img title="Thought Writer Database Tables" src ="images/thought-writer-tables.png" /></p>

\
**POST** /api/thought-writer/post
* Post a thought post by sending the jsonified post content, title, and public status (*true* or *false*) in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I find inspiration in the colors outside.",
    "public": false,
    "title": "The Beauty of Design"
}
```

\
**GET** /api/thought-writer/post/[post_id]
* Retrieve a user's thought post by specifying the post id in the request URL. Note that there must be a verified bearer token for the writer in the request Authorization header for a private post to be retrieved.
* Example response body:
```javascript
{
    "content": "Welcome to Thought Writer, a community post board for you to write your ideas for the world to see. You can also create your own private posts or comment on others' posts. Click the yellow paper icon to get started!",
    "comment_count": 2,
    "created": "2017-10-05T09:53:19.229Z",
    "history": [],
    "modified": "2017-10-05T09:53:19.229Z",
    "post_id": 1,
    "public": true,
    "title": "Welcome",
    "username": "admin"
}
```

\
**PATCH** /api/thought-writer/post/[post_id]
* Update a thought post by sending the post id in the request URL and the jsonified post content, title, and public status (*true* or *false*) in the request body. Note that there must be a verified bearer token for the writer in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I often find inspiration in the color combinations found in nature.",
    "public": true,
    "title": "The Beauty of Design"
}
```

\
**DELETE** /api/thought-writer/post/[post_id]
* Delete a thought post by sending the post id in the request URL. Note that there must be a verified bearer token for the writer in the request Authorization header.

\
**GET** /api/thought-writer/posts?start=[request_start]&end=[request_end]
* Retrieve all users' public thought posts in order of newest to oldest, excluding the webpage owner's posts (the /api/homepage/ideas endpoint should be used for retrieving the owner's public posts). Optionally specify the number of thought posts via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "content": "<font color=\"#00c6fc\"><b>Only when you find yourself can you understand the world and your place within it. To deny oneself would be to have a limited view of the world, as you yourself are part of it not only in perception but in external interfacing and influence.</b></font>",
      "comment_count": 1,
      "created": "2017-10-27T04:31:07.332Z",
      "history": [],
      "modified": "2017-10-27T04:31:07.332Z",
      "post_id": 2,
      "public": true,
      "title": "Finding yourself",
      "username": "greetings23"
    },
    {
      "content": "Welcome to Thought Writer, a community post board for you to write your ideas for the world to see. You can also create your own private posts or comment on others' posts. Click the yellow paper icon to get started!",
      "comment_count": 2,
      "created": "2017-10-05T09:53:19.229Z",
      "history": [],
      "modified": "2017-10-05T09:53:19.229Z",
      "post_id": 1,
      "public": true,
      "title": "Welcome",
      "username": "admin"
    }
]
```

\
**GET** /api/thought-writer/posts/[writer_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's thought posts in order of newest to oldest by specifying the writer's username in the request URL. Optionally specify the number of thought posts via the request URL's start and end query parameters. If there is a verified bearer token for the writer in the request Authorization header, the server will send the user's private and public posts; otherwise, only the public posts will be sent.
* Example response body:
```javascript
[
    {
      "content": "I often find inspiration in the color combinations found in nature.",
      "comment_count": 0,
      "created": "2017-10-27T04:31:07.249Z",
      "modified": "2017-10-28T11:40:12.589Z",
      "history": [
        {
          "content": "I find inspiration in the colors outside.",
          "created": "2017-10-28T11:40:12.589Z",
          "public": false,
          "title": "The Beauty of Design"
        }
      ],
      "post_id": 4,
      "public": false,
      "title": "The Beauty of Design",
      "username": "greetings23"
    },
    {
      "content": "<font color=\"#00c6fc\"><b>Only when you find yourself can you understand the world and your place within it. To deny oneself would be to have a limited view of the world, as you yourself are part of it not only in perception but in external interfacing and influence.</b></font>",
      "comment_count": 1,
      "created": "2017-10-27T04:31:07.332Z",
      "history": [],
      "modified": "2017-10-27T04:31:07.332Z",
      "post_id": 2,
      "public": true,
      "title": "Finding yourself",
      "username": "greetings23"
    }
]
```

\
**POST** /api/thought-writer/comment
* Post a comment to a thought post by specifying the jsonified comment content and the post id in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I really like this post.",
    "post_id": 1
}
```

\
**GET** /api/thought-writer/comment/[comment_id]
* Read a comment to a thought post by specifying the comment id in the request URL. No bearer token is needed in the request Authorization header.
* Example request body:
```javascript
{
    "comment_id": 1,
    "content": "I really like this post.",
    "created": "2017-11-05T02:47:21.413Z",
    "history": [],
    "modified": "2017-11-05T02:47:21.413Z",
    "post_id": 1,
    "username": "esther"
}
```

\
**PATCH** /api/thought-writer/comment/[comment_id]
* Update a comment to a thought post by specifying the comment id in the request URL and the jsonified comment content in the request body. Note that there must be a verified bearer token for the commenter in the request Authorization header.
* Example request body:
```javascript
{
    "content": "I really like this post. Great writing!"
}
```

\
**DELETE** /api/thought-writer/comment/[comment_id]
* Delete a comment to a thought post by specifying the comment id in the request URL. Note that there must be a verified bearer token for the commenter in the request Authorization header.

\
**GET** /api/thought-writer/comments/post/[post_id]?start=[request_start]&end=[request_end]
* Retrieve all comments to a thought post in order of newest to oldest by specifying the post id in the request URL. Optionally specify the number of thought posts via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "comment_id": 3,
      "content": "Anytime!",
      "created": "2017-11-05T03:32:59.182Z"
      "history": [],
      "modified": "2017-11-05T03:32:59.182Z"
      "post_id": 1,
      "username": "admin"
    },
    {
      "comment_id": 2,
      "content": "Thanks for welcoming me!",
      "created": "2017-11-05T02:50:01.246Z"
      "history": [],
      "modified": "2017-11-05T02:50:01.246Z"
      "post_id": 1,
      "username": "esther"
    }
]
```

\
**GET** /api/thought-writer/comments/user/[commenter_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's comments in order of newest to oldest by specifying the commenter's username in the request URL. Optionally specify the number of comments via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
  {
    "comment_id": 6,
    "content": "Wow... I feel the same way.",
    "created": "2017-12-01T01:25:20.435Z"
    "history": [],
    "modified": "2017-12-01T01:25:20.435Z"
    "post_id": 3,
    "post_content": "Sometimes life is hard.",
    "title": "Today I feel...",
    "username": "esther",
    "writer_name": "greetings23"
  },
  {
    "comment_id": 2,
    "content": "Thanks for welcoming me!",
    "created": "2017-11-05T02:50:01.246Z"
    "history": [],
    "modified": "2017-11-05T02:50:01.246Z"
    "post_id": 1,
    "post_content": "Welcome to Thought Writer, a community post board for you to write your ideas for the world to see. You can also create your own private posts or comment on others' posts. Click the yellow paper icon to get started!",
    "title": "Welcome",
    "username": "esther",
    "writer_name": "admin"
  },
  {
    "comment_id": 1,
    "content": "I really like this post. Great writing!",
    "created": "2017-11-05T02:47:21.413Z",
    "history": [
      {
        "content": "I really like this post.",
        "created": "2017-11-05T02:47:21.413Z"
      }
    ],
    "modified": "2017-11-05T03:15:16.003Z",
    "post_id": 2,
    "post_content": "<font color=\"#00c6fc\"><b>Only when you find yourself can you understand the world and your place within it. To deny oneself would be to have a limited view of the world, as you yourself are part of it not only in perception but in external interfacing and influence.</b></font>",
    "title": "Finding yourself",
    "username": "esther",
    "writer_name": "greetings23"
  }
}
```


## Shapes in Rain API
#### September 2017 - Present
[Shapes in Rain](https://shapes-in-rain.crystalprism.io/index.html) is a game in which random shapes appear periodically on the page for a user to clear with a click. Shapes in Rain information is stored in the "shapes_score" database table:
<p align="center"><img title="Shapes in Rain Database Table" src ="images/shapes-table.png" /></p>

\
**POST** /api/shapes-in-rain/score
* Post a score by sending the jsonified score in the request body. Note that there must be a verified bearer token in the request Authorization header.
* Example request body:
```javascript
{
    "score": 30
}
```

\
**GET** /api/shapes-in-rain/score/[score_id]
* Retrieve a score by sending the score id in the request URL. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
{
    "created": "2017-10-24T00:00:23.591Z",
    "score": 30,
    "score_id": 6,
    "username": "esther"
},
```

\
**DELETE** /api/shapes-in-rain/score/[score_id]
* Delete a score by sending the score id in the request URL. Note that there must be a verified bearer token for the player in the request Authorization header.

\
**GET** /api/shapes-in-rain/scores?start=[request_start]&end=[request_end]
* Retrieve all users' game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "created": "2017-10-29T00:10:35.382Z",
      "score": 150,
      "score_id": 20,
      "username": "esther"
    },
    {
      "created": "2017-10-28T08:11:34.113Z",
      "score": 95,
      "score_id": 18,
      "username": "admin"
    },
    {
      "created": "2017-10-20T00:00:23.591Z",
      "score": 30,
      "score_id": 6,
      "username": "esther"
    },
    {
      "created": "2017-10-24T08:30:10.296Z",
      "score": 29,
      "score_id": 11,
      "username": "esther"
    },
    {
      "created": "2017-10-23T09:24:50.404Z",
      "score": 28,
      "score_id": 9,
      "username": "admin"
    }
]
```

\
**GET** /api/shapes-in-rain/scores/[player_name]?start=[request_start]&end=[request_end]
* Retrieve all of a single user's game scores, in order of highest to lowest score. Optionally specify the number of scores via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "created": "2017-10-29T00:10:35.382Z",
      "score": 150,
      "score_id": 20,
      "username": "esther"
    }
    {
      "created": "2017-10-20T00:00:23.591Z",
      "score": 30,
      "score_id": 6,
      "username": "esther"
    },
    {
      "created": "2017-10-24T08:30:10.296Z",
      "score": 29,
      "score_id": 11,
      "username": "esther"
    }
]
```


## User Account API
#### September 2017 - Present
Users who want to join the Crystal Prism community can create an account to store their Shapes in Rain and Rhythm of Life scores, their CanvaShare drawings, and their Thought Writer posts and comments. Users can download all of their data whenever they want to. User information is stored in the "cp_user" database table:
<p align="center"><img title="User Database Table" src ="images/user-table.png" /></p>

\
**POST** /api/user
* Create a user account by sending the jsonified username and password in the request body.
* Example request body:
```javascript
{
    "password": "password"
    "username": "username",
}
```

\
**GET** /api/user/[username]
* Retrieve a user's account information. If there is a verified bearer token for the user in the request Authorization header, the server will send the user's private and public information; otherwise, only the public information will be sent.
* Example response body:
```javascript
{
    "about": "", // User-entered blurb that appears on public profile
    "background_color": "#ffffff", // User-chosen background color of public profile
    "created": "2017-10-04T00:00:00.000Z", // UTC timestamp of when user account was created
    "comment_count": 1, // Number of post comments user has created
    "drawing_count": 1, // Number of drawings user has created
    "drawing_like_count": 1, // Number of drawings user has liked
    "email": "", // User-entered on My Account page; only returned if verified bearer token for the user is included or if "email_public" is True
    "email_public": false, // User specifies if email is viewable on public profile; only returned if verified bearer token for the user is included
    "first_name": "", // User-entered on My Account page; only returned if verified bearer token for the user is included or if "name_public" is true
    "icon_color": "#000000", // User-chosen icon color of public profile
    "last_name": "", // User-entered on My Account page; only returned if verified bearer token for the user is included or if "name_public" is true
    "name_public": false, // User specifies if name is viewable on public profile; only returned if verified bearer token for the user is included
    "post_count": 10, // Number of posts user has created
    "rhythm_high_score": 0, // User's high score for Rhythm of Life
    "rhythm_score_count": 0, // Number of times user has played Rhythm of Life
    "shapes_high_score": 0, // User's high score for Shapes in Rain
    "shapes_score_count": 0, // Number of times user has played Shapes in Rain
    "status": "active", // Can be active or deleted
    "username": "admin" // Case-sensitive username
}
```

\
**PATCH** /api/user/[username]
* Update a user's account information by specifying the jsonified account updates in the request body. Note that there must be a verified bearer token for the user in the request Authorization header.
* Example request body:
```javascript
{
    "about": "Founder of Crystal Prism",
    "background_color": "#9fffad",
    "email": "",
    "email_public": false,
    "first_name": "",
    "icon_color": "#ffb4e6",
    "last_name": "",
    "password": "",
    "name_public": false,
    "username": "esther"
}
```

\
**DELETE** /api/user/[username]
* Soft-delete a user's account as the user (i.e., change the account's status to "deleted" while leaving drawings, posts, comments, scores, personal information, etc. intact, in case the user wants to reactivate the account). Note that there must be a verified bearer token for the user in the request Authorization header.

\
**GET** /api/user/data/[username]
* Retrieve all of a user's data (drawings, posts, comments, scores, personal information, etc.) in a downloadable zip file. Note that there must be a verified bearer token for the user in the request Authorization header.

\
**DELETE** /api/user/data/[username]
* Hard-delete a user's account and their data as the user or as an admin user (i.e., delete all of the user's drawings, posts, comments, scores, personal information, etc. in addition to changing the account status to "deleted"). Note that there must be a verified bearer token for the user or for an admin user in the request Authorization header.

\
**GET** /api/user/verify
* Check if a bearer token in a request Authorization header is valid and receive the expiration time (in seconds since epoch) if so.
* Example response body:
```javascript
{
    "exp": 1509855369,
    "username": "esther"
}
```

\
**GET** /api/users?start=[request_start]&end=[request_end]
* Retrieve all users' usernames. Optionally specify the number of users via the request URL's start and end query parameters. Note that there must be a verified bearer token in the request Authorization header.
* Example response body:
```javascript
[
    "esther",
    "user"
]
```

\
**GET** /api/login
* Check if a username and password in a request Authorization header match the username and password stored for a user account and receive a [JSON Web Token](https://jwt.io/) if so. The JWT is set to expire after 1 hour.
* Example response body:
```javascript
{
    "token": "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVC..."
}
```


## Homepage API
#### February 2018 - Present
The Crystal Prism homepage has an Ideas page that displays Thought Writer posts written by the webpage owner. It also has a Photos page that displays photos I have taken that are stored in a Cloudflare R2 bucket. I use boto3 against R2's S3-compatible API to list the stored photo objects under `photos/`. Note that the following environment variables must be set:
  - "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY" and "R2_BUCKET" must be set to your Cloudflare R2 account, API token credentials and bucket name
  - "R2_PUBLIC_BASE" must be set to the bucket's public URL (e.g., 'https://pub-<id>.r2.dev')

\
**GET** /api/homepage/ideas?start=[request_start]&end=[request_end]
* Retrieve public thought posts written by the webpage owner in order of newest to oldest. Optionally specify the number of thought posts via the request URL's start and end query parameters. No bearer token is needed in the request Authorization header.
* Example response body:
```javascript
[
    {
      "content": "Welcome to my homepage! Click the different menu buttons to see my work. You can contact me using the information on the About page.",
      "created": "2018-3-20T05:18:13.454Z",
      "history": [],
      "post_id": 11,
      "title": "Welcome",
      "username": "esther"
    }
]
```

\
**GET** /api/homepage/photos?start=[request_start]&end=[request_end]
* Retrieve URLs for photos stored in an S3 bucket. Optionally specify the number of photos via the request URL's start and end query parameters.
* Example response body:
```javascript
[
    'https://pub-<id>.r2.dev/photos/1.png',
    'https://pub-<id>.r2.dev/photos/10.png',
    'https://pub-<id>.r2.dev/photos/2.png',
    'https://pub-<id>.r2.dev/photos/3.png',
    'https://pub-<id>.r2.dev/photos/4.png',
    'https://pub-<id>.r2.dev/photos/5.png',
    'https://pub-<id>.r2.dev/photos/6.png',
    'https://pub-<id>.r2.dev/photos/7.png',
    'https://pub-<id>.r2.dev/photos/8.png',
    'https://pub-<id>.r2.dev/photos/9.png'
]
```


## Crystal Prism Database
#### February 2018 - Present
The Crystal Prism database is a PostgreSQL database that contains Crystal Prism user accounts and user data (game scores, drawings, posts, identifying information, etc.). The database is structured as follows:
<p align="center"><img title="Crystal Prism Database" src ="images/cp-database.png" /></p>

Note that all fields in the database tables are required except for those denoted with an asterisk.
The API itself does not back up the database; back it up externally with `pg_dump` on a schedule (the live database is dumped nightly).
