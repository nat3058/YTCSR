# def match_comments(orig_file, reply_file, output_file):
#     """
#     Match the original comments with their corresponding sub-replies.

#     Args:
#         orig_file (str): Path to the file containing the original comments.
#         reply_file (str): Path to the file containing the original comments with sub-replies.
#         output_file (str): Path to the output file.

#     Returns:
#         None
#     """
#     # Read the original comments into a list
#     with open(orig_file, 'r') as f:
#         orig_comments = [line.strip() for line in f.readlines()]

#     # Read the reply file into a list of lines
#     with open(reply_file, 'r') as f:
#         reply_lines = [line.strip() for line in f.readlines()]

#     # Initialize an empty dictionary to store the comments and their sub-replies
#     comment_replies = {}

#     # Initialize an index to keep track of the current original comment
#     comment_index = 0

#     # Open the output file for writing
#     with open(output_file, 'w') as f:
#         # Iterate over the reply lines
#         for line in reply_lines:
#             # If the line matches the current original comment, add it to the dictionary
#             if line == orig_comments[comment_index]:
#                 comment_replies[line] = []
#                 f.write(f"> {line}\n")  # Write original comment with '>' symbol
#             # If the line is a sub-reply, add it to the list of sub-replies for the current original comment
#             elif line in orig_comments:
#                 comment_index += 1
#                 comment_replies[line] = []
#                 f.write(f"> {line}\n")  # Write original comment with '>' symbol
#             else:
#                 comment_replies[orig_comments[comment_index]].append(line)
#                 f.write(f"  {line}\n")  # Write sub-reply with indentation



# # Example usage
# orig_file = "comments.txt"#'original_comments.txt'
# reply_file = "comments_with_sr.txt"#'comments_with_replies.txt'
# output_file = 'outputCSR.txt'

# match_comments(orig_file, reply_file, output_file)



def match_comments(orig_file, reply_file, output_file, json_file, json_lines_file):
    """
    Match the original comments with their corresponding sub-replies.

    Args:
        orig_file (str): Path to the file containing the original comments.
        reply_file (str): Path to the file containing the original comments with sub-replies.
        output_file (str): Path to the output file.
        json_file (str): Path to the JSON output file.
        json_lines_file (str): Path to the JSON lines output file.

    Returns:
        None
    """
    import json

    # Read the original comments into a list
    with open(orig_file, 'r') as f:
        orig_comments = [line.strip() for line in f.readlines()]

    # Read the reply file into a list of lines
    with open(reply_file, 'r') as f:
        reply_lines = [line.strip() for line in f.readlines()]

    # Initialize an empty dictionary to store the comments and their sub-replies
    comment_replies = {}

    # Initialize an index to keep track of the current original comment
    comment_index = 0

    # Open the output file for writing
    with open(output_file, 'w') as f:
        # Iterate over the reply lines
        for line in reply_lines:
            # If the line matches the current original comment, add it to the dictionary
            if line == orig_comments[comment_index]:
                comment_replies[line] = []
                f.write(f"> {line}\n")  # Write original comment with '>' symbol
            # If the line is a sub-reply, add it to the list of sub-replies for the current original comment
            elif line in orig_comments:
                comment_index += 1
                comment_replies[line] = []
                f.write(f"> {line}\n")  # Write original comment with '>' symbol
            else:
                comment_replies[orig_comments[comment_index]].append(line)
                f.write(f"  {line}\n")  # Write sub-reply with indentation

    # Create a JSON-compatible dictionary
    json_data = [{"original_comment": comment, "subreplies": replies} for comment, replies in comment_replies.items()]

    # Open the JSON file for writing
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=4)

    # Open the JSON lines file for writing
    with open(json_lines_file, 'w') as f:
        for item in json_data:
            f.write(json.dumps(item) + "\n")

# Example usage


orig_file = "comments.txt"#'original_comments.txt'
reply_file = "comments_with_sr.txt"#'comments_with_replies.txt'
output_file = 'outputCSR.txt'
json_file = 'outputCSR.json'
json_lines_file = 'outputCSR.jsonl'

match_comments(orig_file, reply_file, output_file, json_file, json_lines_file)
