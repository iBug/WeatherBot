import main


def lambda_main(event, context):
    from types import SimpleNamespace
    args = SimpleNamespace(**event)
    main.main(args)
    return {
        'statusCode': 200,
        'body': "OK\n"
    }
