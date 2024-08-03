# Сообщения для старта и справки
START_MESSAGES: dict[str, str] = {
    "/start": "<b>👋 Привет, {first_name}!</b>\n\n"
              "<i>💳 Здесь вы можете покупать, продавать, хранить и оплачивать с помощью своего кошелька.</i>\n\n"
              "<i>🤖 Бот в настоящее время использует сеть Solana:</i>\n"
              "<i>{node}</i>"
              "\n\n❓ Чтобы просмотреть список доступных команд, введите /help 😊",
}

# Справочное сообщение бота
HELP_MESSAGES: dict[str, str] = {
    "/help": "<b>Описание функционала бота:</b>\n\n"
             "🔑 <b>Создать кошелек:</b>\n\n<i>Позволяет создать новый кошелек Solana."
             "После создания кошелька вы получите закрытый ключ, который следует надежно хранить."
             "Этот закрытый ключ необходим для любых транзакций или взаимодействий с вашим кошельком.</i>\n\n"
             "🔗<b> Подключить кошелек:</b>\n\n<i>Позволяет подключить существующий кошелек Solana к вашей учетной записи."
             "Вам будет предложено ввести адрес кошелька, имя и необязательное описание.</i>\n\n"
             "💰<b> Показать баланс:</b>\n\n<i>Позволяет проверить баланс всех подключенных кошельков.</i>\n\n"
             "📲<b> Перевод токена:</b>\n\n<i>Переводит токены между кошельками Solana. Выберите отправителя, введите "
             "ключ, адрес и сумма. После подтверждения токены будут переведены. Обратите внимание, что для успешного "
             "перевода, отправитель должен иметь достаточный баланс.</i>"
             "\п\п"
             "<b>📜 Просмотр истории транзакций:</b>\n\n<i>Позволяет просматривать историю транзакций для одного из ваших "
             "зарегистрированные кошельки Solana. После выбора нужного кошелька из списка бот отобразит "
             "история входящих и исходящих транзакций для этого кошелька, включая подробную информацию о каждой транзакции"
             "например, уникальный идентификатор транзакции, адреса отправителя и получателя, а также сумма транзакции.</i>"
}

# Кнопки главного меню
MAIN_MENU_BUTTONS: dict[str, str] = {
    "create_wallet": "🔑 Создать новый кошелёк",
    "create_wallet_from_seed": "🔑 Создать новый кошелёк из seed фразы",
    "connect_wallet": "🔗 Подключить существующий кошелёк",
    "balance": "💰 Показать баланс",
    # "token_price": "💹 Show token price",
    # "token_buy": "💸 Buy token",
    # "token_sell": "💳 Sell tokens",
    "token_transfer": "📲 Перевести токен",
    "transaction": "📜 Просмотреть историю транзакций",
    "delete_wallet": "🗑️ Удалить кошелёк",
    # "settings": "⚙️ Crypto wallet settings",
    # "donate": "💝 Donate to the team",
}

# Дополнительные кнопки
OTHER_BUTTONS: dict[str, str] = {
    "button_back": "⬅️ назад",
    "back_to_main_menu": "<b>🏠 Главное меню</b>\n\n"
                         "<i>Чтобы просмотреть список доступных команд, введите /help 😊</i>",
    "save_wallet": "<i>Да</i>",
    "cancel": "<i>Нет</i>",
}

# Сообщения для создания кошелька
CREATE_WALLET_MESSAGE = {
    "create_name_wallet": "💼 <b>Пожалуйста, введите имя вашего кошелька:</b>",
    "wallet_name_confirmation": "💼 <b>Имя вашего кошелька:</b> {wallet_name}",
    "create_description_wallet": "💬 <b>Теперь введите описание вашего кошелька:</b>",
    "wallet_created_successfully": "🎉 <b>Кошелек успешно создан!</b>\n"
                                   "<b><i>Имя кошелька:</i> {wallet_name}</b>\n"
                                   "<b><i>Описание кошелька:</i> {wallet_description}</b>\n"
                                   "<b><i>Адрес кошелька:</i> {wallet_address}</b>\n"
                                   "<b><i>Приватный ключ:</i> {private_key}</b>\n"
                                   "<b><i>Seed фраза:</i> {seed_phrase}</b>\n",
    "invalid_wallet_name": "❌ <b>Введено неверное имя кошелька.</b>\n"
                           "Пожалуйста, введите верное имя для вашего кошелька.",
    "invalid_wallet_description": "❌ <b>Введено неверное описание кошелька.</b>\n"
                                  "Пожалуйста, введите корректное описание вашего кошелька.",
    "create_new_name_wallet": "💼 <b>Введите новое имя для подключенного кошелька:</b>",
    "create_seed_wallet": "💼 <b>Пожалуйста, введите seed фразу:</b>",
    "wallet_seed_confirmation": "💼 <b>Seed фраза вашего кошелька:</b> {seed_phrase}",
    "invalid_wallet_seed": "❌ <b>Введена неверная seed фраза кошелька.</b>\n"
                           "Пожалуйста, введите корректную seed фразу для вашего кошелька.",
}

# Сообщения для 'connect_wallet'
CONNECT_WALLET_MESSAGE = {
    "connect_wallet_address": "<b>🔑 Введите адрес кошелька для подключения к боту</b>",
    "connect_wallet_add_name": "<b>💼 Пожалуйста, введите имя вашего кошелька</b>",
    "connect_wallet_add_description": "💬 <b>Теперь введите описание вашего кошелька.:</b>",
    "invalid_wallet_address": "<b>❌ Неверный адрес кошелька</b>",
    "wallet_connected_successfully": "<b>🎉 Кошелек с адресом:</b>\n"
                                     "<b><i>{wallet_address}</i></b>\n"
                                     "<b>успешно подключен к боту!</b>",
    "this_wallet_already_exists": "<i>Этот адрес кошелька уже был подключен ранее</i>",
}

# Сообщения для обработки команды balance
BALANCE_MESSAGE = {
    "no_registered_wallet": "<b>🛑 У вас нет зарегистрированного кошелька.</b>",
    "balance_success": "<b>💰 Баланс вашего кошелька:</b> {balance} SOL"
}

# Сообщения для переноса
TOKEN_TRANSFER_TRANSACTION_MESSAGE = {
    "transfer_recipient_address_prompt": "<b>📬 Введите адрес кошелька получателя:</b>\n\n"
                                         "Примечание. Минимальный баланс получателя.\n"
                                         "должно быть по крайней мере 0.00089784 SOL",
    "list_sender_tokens": "<b>📋 Ваш список токенов:</b>\n\n<i>Кликните на соответствующий токен:</i>",
    "transfer_amount_prompt": "<b>💸 Введите количество токенов для перевода:</b>",
    "invalid_wallet_address": "<b>❌ Не корректный адрес кошелька.</b>",
    "transfer_successful": "<b>✅ Перевод {amount} SOL\n\n<i>{recipient}</i>\n\n прошёл успешно.</b>",
    "transfer_not_successful": "<b>❌ Не удалось перевести {amount} SOL на\n\n<i>{recipient}.</i></b>",
    "insufficient_balance": "<b>❌ В вашем кошельке недостаточно средств для этого перевода.</b>",
    "insufficient_balance_recipient": "<b>❌ Баланс получателя\nдолжен составлять не менее 0,00089784 SOL.</b>",
    "no_wallet_connected": "<b>🔗 Пожалуйста, подключите свой кошелек перед передачей токенов.</b>",
    "list_sender_wallets": "<b>📋 Список ваших кошельков:</b>\n\n<i>Нажмите на соответствующий кошелек:</i>",
    "choose_sender_wallet": "<b>🔑 Введите адрес вашего кошелька:</b>",
    "invalid_wallet_choice": "<b>❌ Ошибка при выборе кошелька.</b>",
    "no_wallets_connected": "<b>❌ У вас нет подключенных кошельков.\n"
                            "<i>Подключите кошелек перед передачей токенов.</i></b>",
    "save_new_wallet_prompt": "<b>💾 Сохраните этот адрес кошелька:</b> ",
    "wallet_info_template": "{number}) 💼 {name} 📍 {address}\n"
                            "           Solana 💼 SOL 💰 {balance}\n",
    "wallet_info_spl_token_template": "   {name} 💼 {symbol} 💰 {amount}\n",
    "token_info_template": "{name} 💼 {symbol} 💰 {amount}",
    "invalid_amount": "<b>❌ Не корректное количество.</b>",
    "transfer_sender_private_key_prompt": "<b>Введите приватный ключ или начальную фразу для этого кошелька:</b>",
    "invalid_private_key": "<b>❌ Не корректный приватный ключ.</b>",
    "invalid_seed_phrase": "<b>❌ Не корректная seed фраза.</b>",
    "empty_history": "😔 История транзакций пустая.",
    "server_unavailable": "Сервер в настоящее время недоступен. Пожалуйста, повторите попытку позже.",
    "transaction_info": "<b>💼 Транзакция:</b> {transaction_id}:\n"
                        "<b>📲 Отправитель:</b> {sender}\n"
                        "<b>📬 Получатель:</b> {recipient}\n"
                        "<b>💰 Количество:</b> {amount_in_sol} SOL"
}

# Сообщения для удаления кошелька
DELETE_WALLET_MESSAGE = {
    "button_delete_confirmation": "Удалить",
    "delete_wallet_confirmation": "Подтвердите удаление",
    "delete_wallet_successful": "💼 Кошелёк \n<i>{wallet_address}</i>\n <b>успешно</b> удалён",
    "delete_wallet_not_successful": "💼 <b>Удалить кошелёк \n<i>{wallet_address}</i>\n <b>не удалось</b></b>",
}

# Неизвестный ввод сообщения
UNKNOWN_MESSAGE_INPUT = {
    "unexpected_message": "<b>❓ Неизвестная команда или сообщение.</b>\n\n"
                          "Пожалуйста, используйте одну из доступных команд\n"
                          "или варианты из меню.",
    "unexpected_input": "❌ <b>Неожиданный ввод</b>\n\n"
                        "Пожалуйста, выберите действие из меню\n"
                        "или введите одну из доступных команд,\n"
                        "например, /start или /help."
}

TRANSLATION_RU: dict[str, str] = {**CREATE_WALLET_MESSAGE, **OTHER_BUTTONS, **CONNECT_WALLET_MESSAGE, **HELP_MESSAGES,
                           **BALANCE_MESSAGE, **MAIN_MENU_BUTTONS, **START_MESSAGES, **UNKNOWN_MESSAGE_INPUT,
                           **TOKEN_TRANSFER_TRANSACTION_MESSAGE, **DELETE_WALLET_MESSAGE}
