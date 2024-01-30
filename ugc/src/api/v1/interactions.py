from uuid import UUID

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from api.decorators import login_fullcheck_required
from services.bookmark_service import BookmarkService, get_bookmark_service
from services.like_service import LikeService, get_like_service
from services.review_service import ReviewService, get_review_service

from models.interactions import Rating, Review

router = APIRouter()


'''
# BOOKMARK ENDPOINTS
'''
@router.get(
    "/my_bookmarks",
    summary="Get bookmarks",
    status_code=HTTPStatus.OK,
    description="Get current user bookmarmks",
)
async def user_bookmarks(
    request: Request,
    nosql: BookmarkService = Depends(get_bookmark_service)
):
    return JSONResponse(await nosql.get_bookmarked_films_by_user(UUID(request.state.user_id)))


@router.post(
    "/set_bookmark",
    summary="Set bookmark",
    status_code=HTTPStatus.CREATED,
    description="Adding film to favorites",
    dependencies=[Depends(login_fullcheck_required)],
)
async def set_bookmark(
    request: Request,
    film_id: UUID,
    nosql: BookmarkService = Depends(get_bookmark_service)
):
    return JSONResponse(await nosql.insert_film_bookmark(
        UUID(request.state.user_id),
        film_id
    ))


@router.post(
    "/remove_bookmark",
    summary="Remove bookmark",
    status_code=HTTPStatus.OK,
    description="Remove film from favorites",
    dependencies=[Depends(login_fullcheck_required)],
)
async def remove_bookmark(
    request: Request,
    film_id: UUID,
    nosql: BookmarkService = Depends(get_bookmark_service)
):
    return JSONResponse(await nosql.remove_bookmark(
        UUID(request.state.user_id),
        film_id
    ))


'''
# REVIEW ENDPOINTS
'''
@router.post(
    "/add_review",
    summary="Add review",
    status_code=HTTPStatus.CREATED,
)
async def add_review(
    review: Review,
    request: Request,
    nosql: ReviewService = Depends(get_review_service),
    dependencies=[Depends(login_fullcheck_required)],
):
    return JSONResponse(await nosql.insert_review_text(
        UUID(request.state.user_id),
        review.film_id,
        review.review_text
    ))


@router.post(
    "/remove_review",
    summary="Remove review",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(login_fullcheck_required)],
)
async def remove_review(
    film_id: UUID,
    request: Request,
    nosql: ReviewService = Depends(get_review_service)
):
    return JSONResponse(await nosql.remove_review(
        UUID(request.state.user_id),
        film_id
    ))


@router.post(
    "/update_review",
    summary="Update review",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(login_fullcheck_required)],
)
async def update_review(
    review: Review,
    request: Request,
    nosql: ReviewService = Depends(get_review_service)
):
    return JSONResponse(await nosql.update_review_text(
        UUID(request.state.user_id),
        review.film_id,
        review.review_text
    ))


'''
Like endpoints
'''
@router.get(
    "/review_likes",
    summary="Get review likes/dislikes",
    status_code=HTTPStatus.OK,
)
async def review_likes(
    review_id: str,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.get_review_likes_dislikes_count(review_id))


@router.get(
    "/film_likes",
    summary="Get film likes/dislikes",
    status_code=HTTPStatus.OK,
)
async def film_likes(
    film_id: UUID,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.get_film_likes_dislikes_count(film_id))


@router.post(
    "/rate_review",
    summary="Like/dislike review",
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(login_fullcheck_required)],
)
async def rate_review(
    review_id: str,
    is_like: bool,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.insert_review_like_dislike(
        UUID(request.state.user_id),
        review_id,
        is_like
    ))


@router.post(
    "/rate_film",
    summary="Like/dislike film",
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(login_fullcheck_required)],
)
async def rate_film(
    film_id: UUID,
    is_like: bool,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.insert_film_like_dislike(
        UUID(request.state.user_id),
        film_id,
        is_like
    ))


@router.post(
    "/estimate_film",
    summary="Set my film rating",
    status_code=HTTPStatus.CREATED,
    dependencies=[Depends(login_fullcheck_required)],
)
async def estimate_film(
    rating: Rating,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.insert_rating(
        UUID(request.state.user_id),
        rating.film_id,
        rating.rating
    ))


@router.post(
    "/remove_film_like",
    summary="Remove film like",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(login_fullcheck_required)],
)
async def remove_film_like(
    film_id: UUID,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.remove_film_like(
        UUID(request.state.user_id),
        film_id,
    ))


@router.post(
    "/remove_review_like",
    summary="Remove review like",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(login_fullcheck_required)],
)
async def remove_review_like(
    review_id: str,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.remove_review_like(
        UUID(request.state.user_id),
        review_id,
    ))


@router.get(
    "/film_rating",
    summary="Film rating",
    status_code=HTTPStatus.OK,
)
async def film_rating(
    film_id: UUID,
    request: Request,
    nosql: LikeService = Depends(get_like_service)
):
    return JSONResponse(await nosql.get_average_film_rating(film_id))
