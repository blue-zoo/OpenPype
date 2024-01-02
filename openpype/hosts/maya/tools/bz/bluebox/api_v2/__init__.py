import hashlib
import logging
import os
from shutil import copyfile
from tempfile import gettempdir
from uuid import uuid4
from getpass import getuser

import requests

from . import exc
from .threading import ThreadedSession
from .session import Session, get_current_application, get_session
from ..constants import ICON_LIBRARY
from ..everything_else import get_trailing_number
from ... import inflection


logger = logging.getLogger('bluebox')


@Session.wrap
def generate_exec_command(identifier, environment=None, category=None, collection=None,
                          use_globals=False, show_code=True, _=None, session=None):
    """Generate a command to run the script."""
    call_id = (_ + ':') if _ else ''
    script = session.get('scripts', identifier, _=call_id + 'b0fa8134-5ea5-435b-a861-1e482466c9b2')

    # Build command string
    if script['author'] is None:
        command = ['# Script {!r}'.format(script['name'])]
    else:
        command = ['# Script {!r} by {!r}'.format(script['name'], script['author'])]
    command.append('from openpype.hosts.maya.tools.bz.bluebox import api_v2')
    args = [identifier]
    kwargs = {}
    if environment is not None:
        kwargs['environment'] = environment
    if category is not None:
        kwargs['category'] = category
    if collection is not None:
        kwargs['collection'] = collection

    args = ', '.join(repr(arg) for arg in args)
    kwargs = ', '.join('{}={!r}'.format(k, v) for k, v in kwargs.items())
    command.append('api_v2.exec_({}{}, _={})'.format(
        ', '.join(filter(bool, (args, kwargs))),
        ', globals_=globals()' if use_globals else '',
        call_id + '88ad5b62-cab7-4b32-b9e4-b38e156d5b67',
    ))
    if show_code:
        code = session.get('script-revisions', script=identifier, version='latest', state='Stable',
                           _=call_id + '90669700-00fa-4ac7-b5d0-1093c9ad1378')[0]['code']
        command += ['', '# -------- Script --------']
        for line in code.strip('\n').split('\n'):
            command.append('# ' + line)
    return '\n'.join(command) + '\n'


@Session.wrap
def get_icon(endpoint, primary_key, _=None, session=None):
    """Get the icon path from a model.
    Multiple inputs can be used to fall back on if needed.
    """
    if endpoint is None:
        return primary_key
    call_id = (_ + ':') if _ else ''

    try:
        item = session.get(endpoint, primary_key, _=call_id + '5ea962aa-876e-4076-808d-22fee97e1351')
    except exc.ResultNotFoundError:
        return None

    if item['icon'] is not None:
        try:
            return session.get('icons', item['icon'], _=call_id + '9412732e-30ef-4ed5-a7aa-8fcbf8f7b410')['path']
        except exc.CacheNotFoundError:
            pass

    if endpoint == 'collections':
        if item['identifier'].startswith('named'):
            short_name = item['identifier'].split('.')[1]
            path = resource.icon('Projects/{}.png'.format(short_name), warn=False)
            if path is not None:
                return path

        elif item['identifier'].startswith('personal'):
            username = item['identifier'].split('.')[1]
            path = get_icon('users', username, session=session)
            if path is not None:
                return path

        return resource.icon('bluebox.png')

    elif endpoint == 'categories':
        if item['parent'] is None:
            return get_icon('collections', item['collection'], session=session)
        return get_icon('categories', item['parent'], session=session)

    elif endpoint == 'users':
        return resource.icon('no_photo.png')

    return None


@Session.wrap
def can_execute_script(script, session=None):
    """Determine if the script can run under the current environment."""
    application, version = get_current_application()
    try:
        scriptAppVersions = session.get('script-applications', script=script, application=application,
                                        _='ee36ecc9-4040-4dd7-95c5-2b2e451ff4cc')

    # Fallback if API is down
    # Attempt to directly read the script data
    except exc.CacheNotFoundError as e:
        try:
            script = session.get('script', script, _='e1a891ac-1092-42d1-a78b-91e9582a40d5')
        except exc.CacheNotFoundError as e:
            return False
        if application not in script['applications']:
            return None

        scriptAppVersions = [dict(
            min_version=script['applications'][application]['min'],
            max_version=script['applications'][application]['max'],
        )]

    # Application not added anyway
    if not scriptAppVersions:
        return False

    # Skip the version check for certain apps
    if version is None:
        return True

    # Grab the valid versions
    min_version = scriptAppVersions[0]['min_version']
    max_version = scriptAppVersions[0]['max_version']
    if min_version is None and max_version is None:
        return True

    # Convert from str to the correct type
    if min_version is not None:
        min_version = type(version)(min_version)
    if max_version is not None:
        max_version = type(version)(max_version)

    # Check if the version is within range
    if min_version is not None and min_version > version:
        return False
    if max_version is not None and max_version < version:
        return False

    return True


def generate_api_command(scriptIdentifier, environment='Manual',
                         category=None, collection=None, _=None):
    """Generate the command to execute the script."""
    call_id = (_ + ':') if _ else ''
    kwargs = dict(category=category, collection=collection, _=call_id + 'd728c4bf-3086-4e7b-be0e-e2ff7b3cd9c7')
    kwargs = {k: v for k, v in kwargs.items() if v}

    return (
        'from openpype.hosts.maya.tools.bz.bluebox import api_v2\n'
        'api_v2.exec_({identifier!r}, environment={env!r}, globals_=globals(), {kwargs})'
    ).format(
        identifier=scriptIdentifier,
        env=environment,
        kwargs=', '.join('{}={!r}'.format(k, v) for k, v in kwargs.items()),
    )


def _run_python(revision, globals_=None):
    """Execute a Python script."""
    if globals_ is None:
        globals_ = globals()

    name_copy = globals_.get('__name__')
    globals_['__name__'] = '__main__'
    try:
        exec(revision['code'], globals_)  # pylint: disable=exec-used

    except Exception as e:  # pylint: disable=broad-except
        # Special case if this module has been force deleted from memory
        if __name__ is None:
            return dict(success=False, data=None)

        import traceback
        exc = traceback.format_exc()

        # Format the exception to remove not helpful information
        exc = exc.replace(', in <module>', '').replace('File "<string>"', 'Script "{}"'.format(revision['script']))
        exc_lines = exc.split('\n')
        exc = '\n'.join([exc_lines[0]] + exc_lines[3:]).strip('\n')
        logger.error(str(e)+'\n'+exc)

        return dict(success=False, data=exc)

    finally:
        if name_copy is None:
            del globals_['__name__']
        else:
            globals_['__name__'] = name_copy
    return dict(success=True, data=None)


def _run_mel(revision):
    """Execute a MEL script."""
    import maya.mel as mel
    try:
        result = mel.eval(revision['code'])

    except RuntimeError as e:
        # Format the exception to remove not helpful information
        exc = str(e).split('\n', 1)[1]
        line_check = exc.split(': ', 2)[:2]
        try:
            if line_check[0] == line_check[1]:
                exc = exc.split(': ', 1)[1]
        except IndexError:
            pass
        logger.error(exc)

        return dict(success=False, data=exc)
    return dict(success=True, data=result)


def _run_tcl(revision):
    """Execute a Tcl script.
    Attempt to create a node first, if nothing happens then run the script inline.
    """
    import nuke

    code = revision['code'].encode('utf-8')

    # Create temp file
    temp_path = os.path.join(gettempdir(), uuid4().hex + '.tcl')
    logger.debug('Attempting to execute TCL file: %s', temp_path)
    with open(temp_path, 'wb') as f:
        f.write(code)

    try:
        result = nuke.nodePaste(temp_path)
        if result is None:
            logger.debug('No nodes created, attempting to execute code inline...')
            result = nuke.tcl(code)
    except Exception as e:
        exc = str(e)
        logger.error(exc)
        return dict(success=False, data=exc)

    # Clean up temp file
    finally:
        os.remove(temp_path)

    return dict(success=True, data=result)


def _run_vex(revision):
    """Execute a VEX script."""
    import hou

    stdout, stderr = hou.hscript(revision['code'].encode('utf-8'))
    stderr = stderr.lstrip('\r\n')
    if stderr:
        logger.error(stderr)
        return dict(success=False, data=exc)

    return dict(success=True, data=stdout)


@Session.wrap
def _run_script(scriptIdentifier, environment='Manual', category=None,
                collection=None, globals_=None, _=None, session=None):
    call_id = (_ + ':') if _ else ''
    revision = session.get('script-revisions', script=scriptIdentifier, version='latest', state='Stable',
                           _ignore_cache=True, _=call_id + '82d3ec42-d064-4d64-a7fe-722c0a663c11')[0]

    invalid_imports = [
        'from bz',
        'import bz',
        'from lighting'
        'import lighting',
    ]
    if any(imp in revision['code'] for imp in invalid_imports) and 'except' not in revision['code'] and 'openpype' not in revision['code']:
        logger.warning('Script not compatible with Ayon')
        return

    logger.info('Executing %r...', scriptIdentifier)

    # Log execution info
    readonly = False
    payload = dict(command='script-exec',
                   script=scriptIdentifier,
                   environment=environment,
                   category=category,
                   collection=collection)

    if session.offline:
        readonly = True
    else:
        try:
            session.post('user-commands', payload, _=call_id + 'dd31c8a1-6b6c-40a0-bea1-6ac7dbee8bda')
        except (exc.ResponseError, requests.exceptions.RequestException):
            if getuser() == 'peterh':
                raise
            readonly = True

    if revision['language'] == 'Python':
        result = _run_python(revision, globals_=globals_)
    elif revision['language'] == 'MEL':
        result = _run_mel(revision)
    elif revision['language'] == 'Tcl':
        result = _run_tcl(revision)
    elif revision['language'] == 'VEX':
        result = _run_vex(revision)
    else:
        raise NotImplementedError(revision['language'])

    if result.get('success'):
        logger.info('%r successfully executed', scriptIdentifier)
        return result['data']

    else:
        logger.warning('Error executing %r', scriptIdentifier)

        if not readonly and result['data']:
            payload = dict(command='script-error',
                           script=scriptIdentifier,
                           error=result['data'])
            session.post('user-commands', payload, _=call_id + '82243d76-28cd-4cfa-b01f-c5f1caf0a0bb')
    return None


@Session.wrap
def exec_(scriptIdentifier, environment='Manual', parent=None, session=None, **kwargs):
    return _run_script(scriptIdentifier, environment=environment, session=session, **kwargs)


def calculate_icon_hash(path):
    """Get the hash of an icon."""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


@Session.wrap
def suggest_icon_name(path, session=None):
    """Suggest a nice icon name from the filename."""
    iconName = inflection.titleize(os.path.splitext(os.path.basename(path))[0].strip('.'))
    while True:
        try:
            session.get('icons', iconName, _='aa5310e4-f1fb-4806-ad44-6e8803f75419')
        except exc.ResultNotFoundError:
            break

        iteration = get_trailing_number(iconName)
        if iteration is None:
            iconName += str(2)
        else:
            iconName = iconName[:-len(str(iteration))] + str(iteration + 1)
    return iconName


def copy_icon_to_network(path, hash=None):
    """Copy an icon to the global library."""
    if hash is None:
        hash = calculate_icon_hash(path)
    extension = os.path.splitext(path)[1].strip('.')
    new_path = os.path.join(ICON_LIBRARY, hash + '.' + extension)
    if not os.path.exists(new_path):
        copyfile(path, new_path)
    return new_path


@Session.wrap
def copy_collection(old, new, session=None):
    """Copy all the categories and scripts in a collection to another."""
    old_categories = session.get('categories', collection=old, state='Enabled',
                                 _='63c2dff2-0e6c-4f50-9ed1-61e734280c50')
    new_categories = session.get('categories', collection=new, state='Enabled',
                                 _='3bed2eff-f382-4741-a9e9-c2117a4e644d')

    # Remove collection from the category display names
    old_categories = dict(old_categories)
    new_categories = dict(new_categories)
    for category_list in (old_categories, new_categories):
        for category_identifier, category in category_list.items():
            category = category_list[category_identifier] = dict(category)
            category['display_name'] = category['display_name'].split('.', 1)[-1]

    # Create new categories
    new_categories = dict(new_categories)
    for category in sorted(old_categories.values(), key=lambda category: len(category['display_name'])):
        if category['display_name'] in (cat['display_name'] for cat in new_categories.values()):
            continue

        payload = dict(
            name=category['name'],
            description=category['description'],
            collection=new,
            state=category['state'],
            icon=category['icon'],
        )
        if category['parent']:
            old_parent = old_categories[category['parent']]
            payload['parent'] = next(cat_id for cat_id, cat in new_categories.items()
                                     if cat['display_name'] == old_parent['display_name'])
        result = session.post('categories', payload, _='bb5479f1-39da-4c31-8eb2-ef76bd933049')
        logger.info('Created category: %s', result)

        # Emulate data
        new_categories[result] = payload
        current = payload
        stack = [current['name']]
        while current.get('parent'):
            stack.append(current['parent'])
            current = new_categories[current['parent']]
        payload['display_name'] = '.'.join(reversed(stack))

    # Copy over collection scripts
    old_script_collections = session.get('script-collections', collection=old,
                                         _='e6727ef8-d18c-44be-ab7a-ee94cfb8abfb')
    new_script_collections = session.get('script-collections', collection=new,
                                         _='8999b65a-9f98-40fd-9aed-d2bc777282c4')
    current_script_collections = {(sc['script'], sc['collection']) for sc in new_script_collections}

    for sc in old_script_collections:
        payload = dict(
            script=sc['script'],
            collection=new,
        )
        if (payload['script'], payload['collection']) not in current_script_collections:
            session.post('script-collections', payload, _='30bbe17c-0501-4777-9124-9e94dd0e8936')
            logger.info('Added script %r to %r collection', payload['script'], payload['collection'])

    # Copy over category scripts
    old_script_categories = session.get('script-categories', categories=','.join(old_categories),
                                        _='8c6ff83d-6c14-4741-ac6f-098c2e79f767')
    new_script_categories = session.get('script-categories', categories=','.join(new_categories),
                                        _='0e38693a-d022-4f29-bc42-ebd40541ec81')
    current_script_categories = {(sc['script'], sc['category']) for sc in new_script_categories}

    for sc in old_script_categories:
        new_category = next(cat_id for cat_id, cat in new_categories.items()
                            if cat['display_name'] == old_categories[sc['category']]['display_name'])
        payload = dict(
            script=sc['script'],
            category=new_category,
        )
        if (payload['script'], payload['category']) not in current_script_categories:
            session.post('script-categories', payload, _='e3879f49-ce47-41b0-a264-a5e67b9b91fe')
            logger.info('Added script %r to %r category', payload['script'], payload['category'])


def get(*args, **kwargs):
    return Session().get(*args, **kwargs)


def post(*args, **kwargs):
    return Session().post(*args, **kwargs)


def put(*args, **kwargs):
    return Session().put(*args, **kwargs)


def patch(*args, **kwargs):
    return Session().patch(*args, **kwargs)


def delete(*args, **kwargs):
    return Session().delete(*args, **kwargs)


if __name__ == '__main__':
    with Session('http://localhost:5000/v1/') as session:
        data = dict(application='Substance Painter', version_str='8.3', version_int=83)
        print(session.post('application-versions', data))
