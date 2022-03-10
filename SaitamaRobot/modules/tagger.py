# This Module (Tagall) Is Taken From @Saber_herobot

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Filters
from SaitamaRobot.modules.redis import REDIS
from SaitamaRobot.modules.helper_funcs.chat_status import bot_admin, user_admin
from SaitamaRobot.modules.helper_funcs.extraction import extract_user_and_text
from SaitamaRobot.modules.helper_funcs.alternate import typing_action
from SaitamaRobot.modules.helper_funcs.decorators import kaicmd, kaicallback


@kaicmd(command="addtag", pass_args=True, filters=Filters.chat_type.groups)
@bot_admin
@user_admin
@typing_action
def addtag(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return
        raise
    if user_id == context.bot.id:
        message.reply_text("how I supposed to tag myself")
        return

    chat_id = str(chat.id)[1:]
    tagall_list = list(REDIS.sunion(f"tagall2_{chat_id}"))
    match_user = mention_html(member.user.id, member.user.first_name)
    if match_user in tagall_list:
        message.reply_text(
            "{} is already exist in {}'s tag list.".format(
                mention_html(member.user.id, member.user.first_name), chat.title
            ),
            parse_mode=ParseMode.HTML,
        )
        return
    message.reply_text(
        "{} accept this, if you want to add yourself into {}'s tag list! or just simply decline this.".format(
            mention_html(member.user.id, member.user.first_name), chat.title
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Accept", callback_data=f"tagall_accept={user_id}"
                    ),
                    InlineKeyboardButton(
                        text="Decline", callback_data=f"tagall_dicline={user_id}"
                    ),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


@kaicmd(command="removetag", pass_args=True, filters=Filters.chat_type.groups)
@bot_admin
@user_admin
@typing_action
def removetag(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return
        raise
    if user_id == context.bot.id:
        message.reply_text("how I supposed to tag or untag myself")
        return
    chat_id = str(chat.id)[1:]
    tagall_list = list(REDIS.sunion(f"tagall2_{chat_id}"))
    match_user = mention_html(member.user.id, member.user.first_name)
    if match_user not in tagall_list:
        message.reply_text(
            "{} is doesn't exist in {}'s list!".format(
                mention_html(member.user.id, member.user.first_name), chat.title
            ),
            parse_mode=ParseMode.HTML,
        )
        return
    member = chat.get_member(int(user_id))
    chat_id = str(chat.id)[1:]
    REDIS.srem(
        f"tagall2_{chat_id}", mention_html(member.user.id, member.user.first_name)
    )
    message.reply_text(
        "{} is successfully removed from {}'s list.".format(
            mention_html(member.user.id, member.user.first_name), chat.title
        ),
        parse_mode=ParseMode.HTML,
    )


@kaicallback(pattern=r"tagall_")
def tagg_all_button(update, context):
    query = update.callback_query
    chat = update.effective_chat
    splitter = query.data.split("=")
    query_match = splitter[0]
    user_id = splitter[1]
    if query_match == "tagall_accept" and query.from_user.id == int(user_id):
        member = chat.get_member(int(user_id))
        chat_id = str(chat.id)[1:]
        REDIS.sadd(
            f"tagall2_{chat_id}",
            mention_html(member.user.id, member.user.first_name),
        )
        query.message.edit_text(
            "{} is accepted! to add yourself {}'s tag list.".format(
                mention_html(member.user.id, member.user.first_name), chat.title
            ),
            parse_mode=ParseMode.HTML,
        )

    elif (
        query_match == "tagall_accept"
        or query_match == "tagall_dicline"
        and query.from_user.id != int(user_id)
    ):
        context.bot.answer_callback_query(
            query.id, text="You're not the user being added in tag list!"
        )
    elif query_match == "tagall_dicline":
        member = chat.get_member(int(user_id))
        query.message.edit_text(
            "{} is deslined! to add yourself {}'s tag list.".format(
                mention_html(member.user.id, member.user.first_name), chat.title
            ),
            parse_mode=ParseMode.HTML,
        )


@kaicmd(command="untagme", filters=Filters.chat_type.groups)
@typing_action
def untagme(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    chat_id = str(chat.id)[1:]
    tagall_list = list(REDIS.sunion(f"tagall2_{chat_id}"))
    match_user = mention_html(user.id, user.first_name)
    if match_user not in tagall_list:
        message.reply_text(
            "You're already doesn't exist in {}'s tag list!".format(chat.title)
        )
        return
    REDIS.srem(f"tagall2_{chat_id}", mention_html(user.id, user.first_name))
    message.reply_text(
        "{} has been removed from {}'s tag list.".format(
            mention_html(user.id, user.first_name), chat.title
        ),
        parse_mode=ParseMode.HTML,
    )


@kaicmd(command="tagme", filters=Filters.chat_type.groups)
@typing_action
def tagme(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    chat_id = str(chat.id)[1:]
    tagall_list = list(REDIS.sunion(f"tagall2_{chat_id}"))
    match_user = mention_html(user.id, user.first_name)
    if match_user in tagall_list:
        message.reply_text("You're Already Exist In {}'s Tag List!".format(chat.title))
        return
    REDIS.sadd(f"tagall2_{chat_id}", mention_html(user.id, user.first_name))
    message.reply_text(
        "{} has been successfully added in {}'s tag list.".format(
            mention_html(user.id, user.first_name), chat.title
        ),
        parse_mode=ParseMode.HTML,
    )


@kaicmd(command="tagall", filters=Filters.chat_type.groups)
@bot_admin
@user_admin
@typing_action
def tagall(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    query = " ".join(args)
    if not query:
        message.reply_text("Please give a reason why are you want to tag all!")
        return
    chat_id = str(chat.id)[1:]
    tagall = sorted(REDIS.sunion(f"tagall2_{chat_id}"))
    if tagall := ", ".join(tagall):
        tagall_reason = query
        if message.reply_to_message:
            message.reply_to_message.reply_text(
                "{}"
                "\n\n<b>• Tagged Reason : </b>"
                "\n{}".format(tagall, tagall_reason),
                parse_mode=ParseMode.HTML,
            )
        else:
            message.reply_text(
                "{}"
                "\n\n<b>• Tagged Reason : </b>"
                "\n{}".format(tagall, tagall_reason),
                parse_mode=ParseMode.HTML,
            )
    else:
        message.reply_text("Tagall list is empty!")


@kaicmd(command="untagall", filters=Filters.chat_type.groups)
@bot_admin
@user_admin
@typing_action
def untagall(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    chat_id = str(chat.id)[1:]
    tagall_list = list(REDIS.sunion(f"tagall2_{chat_id}"))
    for tag_user in tagall_list:
        REDIS.srem(f"tagall2_{chat_id}", tag_user)
    message.reply_text(
        "Successully removed all users from {}'s tag list.".format(chat.title)
    )


__mod_name__ = "Tagger"

__help__ = """ 
*Tagger* is an essential feature to mention all subscribed members in the group. Any chat members can subscribe to tagger.

*Users Commands:*
>> /tagme: registers to the chat tag list.
>> /untagme: unsubscribes from the chat tag list.

*Admin Commands:*
>> /tagall: mention all subscribed members.
>> /untagall: clears all subscribed members. 
>> /addtag <userhandle>: add a user to chat tag list. (via handle, or reply)
>> /removetag <userhandle>: remove a user to chat tag list. (via handle, or reply)
"""
