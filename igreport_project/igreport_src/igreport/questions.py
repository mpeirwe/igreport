# Questions in various languages
# the keys of dict translations which correspond to languages should be of max length 6
# the spec: http://www.w3.org/International/articles/language-tags/Overview
# reference:http://www.iana.org/assignments/language-subtag-registry
translations = {
    'eng': dict(
        COMPLAINT_QUESTION='Expose Corruption toll free service, what is your complaint?',
        ACCUSED_QUESTION='Please give the name of the person and Organisation you are reporting ONLY',
        DISTRICT_QUESTION='Please send the district where the person works ONLY',
        AMOUNT_QUESTION='What was involved (if money, how much)?',
        NAME_QUESTION='What is your Name?',
        #CONFIRMATION_MESSAGE='Your complaint has been recorded. Your Complaint/ref No is %(reference_number)s. For further queries call 0414347387. Thank you'
        CONFIRMATION_MESSAGE='Your complaint has been successfully recorded. We shall get back to you shortly.'
    ),
    'ite': dict(
        COMPLAINT_QUESTION='Olimo ecamusana kotoma aitijenar naatitai',
        ACCUSED_QUESTION='Itigena ekiror itunganan kede erionget lo itijenaarit ijo',
        DISTRICT_QUESTION='Itijena ebooma / edistrict lo iswamai itunganan ngin',
        AMOUNT_QUESTION='Inyobo iswamauna (Arai erai isiringin idi bo)?',
        NAME_QUESTION='Ingai bo ekiror koni',
        CONFIRMATION_MESSAGE='Adaun adumun angurian kon. Enamba lo angurian kon erai %(reference_number)s. Kanu ijo ajenun acie oramu esimu lota 0414347387. Eyalama noi'     
    ),
    'lug': dict(
        COMPLAINT_QUESTION='Loopa obulyaake kubwerere. Olina kwemulugunya ki?',
        ACCUSED_QUESTION='Kitongole ki oba muntu ki gw\'oloopa?',
        DISTRICT_QUESTION='Oli mu disitulikiti ki?',
        AMOUNT_QUESTION='Ssente meka zebakusabye?',
        NAME_QUESTION='Amanya go gwe ani?',
        CONFIRMATION_MESSAGE='Okwemulugunya kwo tukufunye. Webale nyo. %(reference_number)s'
    )
}
