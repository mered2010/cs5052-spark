from pyspark.sql.functions import col, lower, array_contains, explode, count, mean


def movies_by_ids(spark, ratings, movies, movie_ids):
    """ Returns a dataframe containing details about the movies matching the IDs in movie_ids """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    # Return movies with given IDs
    return movies_agg.where(movies_agg.movieId.isin(movie_ids))


def movies_by_titles(spark, ratings, movies, titles):
    """ Returns a dataframe containing movies with names similar to those in titles """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    return movies_agg.where(lower(movies_agg.title).rlike("|".join(titles)))


def movies_by_user_ids(spark, ratings, movies, user_ids):
    """ Returns a dataframe containing movies watched by users in user_ids """

    # Find ratings made by given users
    filtered_ratings = ratings.where(ratings.userId.isin(
        user_ids))

    # Find distinct movie IDs for each user via found ratings
    users_movies = filtered_ratings.select(
        col("userId"), col("movieId")).distinct()

    return users_movies


def movies_by_genres(spark, ratings, movies, genres):
    """ Returns a dataframe containing movies with genre in their list of genres """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    # Expand genres arrays into multiple rows
    genre_movies = movies_agg.withColumn(
        "genre_temp", explode(movies_agg.genres))

    # Filter movies to genres; Remove expanded genres column & duplicate movies
    genre_movies = genre_movies.filter(genre_movies.genre_temp.isin(genres))\
        .drop("genre_temp").distinct()

    return genre_movies


def movies_by_years(spark, ratings, movies, years):
    """ Returns a dataframe containing movies which were released #
    in a year in provided years """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    return movies_agg.filter(movies_agg.year.isin(years))


def movies_sorted_rating(spark, ratings, movies):
    """ Returns a dataframe containing all movies sorted by average rating  """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    # Order by descending average rating
    movies_agg = movies_agg.sort(
        col("avgRating").desc(), col("ratings").desc())

    return movies_agg


def movies_sorted_watches(spark, ratings, movies):
    """ Returns a dataframe containing all movies sorted by the number of watches """

    # Find aggregate movie data (count & average)
    movies_agg = aggregate_movies(ratings, movies)

    # Order by descending view count
    movies_agg = movies_agg.sort(
        col("ratings").desc(), col("avgRating").desc())

    return movies_agg


def aggregate_movies(ratings, movies):
    """ Returns a dataframe containing the number of ratings and average rating 
    for each movie in movies  """

    # Find ratings for movies
    movies_ratings = ratings.join(
        movies, ratings.movieId == movies.movieId, "inner").select(ratings["*"])

    # Aggregate ratings (count & average)
    rating_aggs = movies_ratings.groupBy(
        "movieId").agg(count("rating"), mean("rating"))

    # Rename columns
    rating_aggs = rating_aggs.withColumnRenamed(
        "count(rating)", "ratings").withColumnRenamed(
            "avg(rating)", "avgRating").withColumnRenamed(
                "movieId", "r_movieId")

    # Join to movies on movieId & remove duplicate ID column
    movies_agg = movies.join(rating_aggs, movies.movieId ==
                             rating_aggs.r_movieId, "left").drop("r_movieId")

    # Replace nulls with 0
    movies_agg = movies_agg.na.fill(0, ["ratings", "avgRating"])

    return movies_agg
